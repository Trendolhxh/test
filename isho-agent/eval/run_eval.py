"""
Eval Runner — 三层流水线：Agent 运行 → 确定性检查 → LLM Judge。

用法:
    python run_eval.py                          # 运行所有画像
    python run_eval.py --profile A              # 只运行画像 A
    python run_eval.py --case A01 A03           # 只运行指定 case
    python run_eval.py --deterministic-only     # 只跑确定性检查（跳过 LLM Judge）
"""

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from graders.deterministic import grade, TraceRecord, GradeReport
from graders.llm_judge import build_judge_messages, JUDGE_OUTPUT_SCHEMA

# ── 配置 ──────────────────────────────────────────────────

EVAL_DIR = Path(__file__).parent
PROFILES = sorted(EVAL_DIR.glob("profile-*.json"))
TRACE_DIR = EVAL_DIR / "traces"
REPORT_DIR = EVAL_DIR / "reports"


# ── 工具函数 ──────────────────────────────────────────────

def load_profiles(filter_profile: str | None = None) -> list[dict]:
    profiles = []
    for p in PROFILES:
        data = json.loads(p.read_text(encoding="utf-8"))
        if filter_profile and data["profile_id"] != filter_profile.upper():
            continue
        profiles.append(data)
    return profiles


def save_trace(trace: TraceRecord, run_id: str):
    """保存完整 trace 到 traces/ 目录。"""
    TRACE_DIR.mkdir(exist_ok=True)
    path = TRACE_DIR / f"{run_id}_{trace.case_id}.json"
    path.write_text(json.dumps({
        "case_id": trace.case_id,
        "tool_calls": trace.tool_calls,
        "response_text": trace.response_text,
        "token_usage": trace.token_usage,
        "agent_loop_rounds": trace.agent_loop_rounds,
    }, ensure_ascii=False, indent=2), encoding="utf-8")


# ── Agent 调用（桩函数，替换为你的实际调用逻辑）─────────────

async def call_agent(case: dict, user_context: dict) -> TraceRecord:
    """
    调用 agent，返回结构化 trace。

    TODO: 替换为你的实际 agent 调用逻辑，需要：
    1. 组装 system prompt + tools + user_context + messages
    2. 调用 agent API
    3. 从响应中提取 tool_calls、response_text、token_usage、loop_rounds
    """
    raise NotImplementedError(
        "请实现 call_agent()，对接你的 agent API。"
        "返回 TraceRecord(case_id, tool_calls, response_text, token_usage, agent_loop_rounds)"
    )


# ── LLM Judge 调用（桩函数）──────────────────────────────

async def call_llm_judge(case: dict, trace: TraceRecord) -> dict:
    """
    调用 LLM Judge，返回结构化评分。

    TODO: 替换为你的实际 LLM 客户端调用。
    """
    raise NotImplementedError(
        "请实现 call_llm_judge()，对接你的 LLM API。"
        "参考 graders/llm_judge.py 中的 judge() 函数。"
    )


# ── 报告生成 ──────────────────────────────────────────────

@staticmethod
def format_table(results: list[dict]) -> str:
    """生成 Markdown 格式的结果表格。"""
    lines = []
    lines.append("| Case | Name | Det. | Outcome | Process | Style | Overall | Flags |")
    lines.append("|------|------|------|---------|---------|-------|---------|-------|")

    for r in results:
        det = r["deterministic"]
        llm = r.get("llm_judge", {})
        flags = []

        if det["hard_fail"]:
            flags.append("🔴 HARD_FAIL")
        if not det["all_passed"]:
            for c in det.get("failed_checks", []):
                flags.append(c)

        flag_str = "; ".join(flags[:3]) if flags else "✅"
        det_str = det["pass_rate"]
        outcome = llm.get("outcome", {}).get("score", "-")
        process = llm.get("process", {}).get("score", "-")
        style = llm.get("style", {}).get("score", "-")
        overall = llm.get("overall_score", "-")

        lines.append(
            f"| {r['case_id']} | {r['case_name'][:20]} | {det_str} | {outcome} | {process} | {style} | {overall} | {flag_str} |"
        )

    return "\n".join(lines)


def generate_report(results: list[dict], run_id: str):
    """生成并保存评测报告。"""
    REPORT_DIR.mkdir(exist_ok=True)

    # 汇总统计
    total = len(results)
    hard_fails = sum(1 for r in results if r["deterministic"]["hard_fail"])
    det_all_pass = sum(1 for r in results if r["deterministic"]["all_passed"])
    llm_scores = [r["llm_judge"]["overall_score"] for r in results if "llm_judge" in r]
    avg_llm = sum(llm_scores) / len(llm_scores) if llm_scores else 0

    summary = {
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "total_cases": total,
        "deterministic_all_pass": det_all_pass,
        "deterministic_hard_fails": hard_fails,
        "llm_judge_avg_score": round(avg_llm, 1),
        "results": results,
    }

    # JSON 报告
    json_path = REPORT_DIR / f"{run_id}.json"
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    # Markdown 报告
    md_lines = [
        f"# Eval Report: {run_id}",
        f"",
        f"- 时间: {summary['timestamp']}",
        f"- 总用例: {total}",
        f"- 确定性检查全通过: {det_all_pass}/{total}",
        f"- 确定性硬性失败: {hard_fails}",
        f"- LLM Judge 平均分: {avg_llm:.1f}",
        f"",
        format_table(results),
        f"",
        f"## 失败详情",
        f"",
    ]

    for r in results:
        if r["deterministic"]["hard_fail"] or not r["deterministic"]["all_passed"]:
            md_lines.append(f"### {r['case_id']} - {r['case_name']}")
            for c in r["deterministic"].get("failed_checks", []):
                md_lines.append(f"- ❌ {c}")
            if "llm_judge" in r:
                for dim in ["outcome", "process", "style"]:
                    note = r["llm_judge"].get(dim, {}).get("note", "")
                    if note:
                        md_lines.append(f"- {dim}: {note}")
            md_lines.append("")

    md_path = REPORT_DIR / f"{run_id}.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    print(f"\n报告已保存:")
    print(f"  JSON: {json_path}")
    print(f"  Markdown: {md_path}")

    return summary


# ── 主流程 ────────────────────────────────────────────────

async def run_case(case: dict, user_context: dict, run_id: str,
                   deterministic_only: bool = False) -> dict:
    """运行单个 case 的完整评测流水线。"""

    # 第 1 层: 调用 agent
    trace = await call_agent(case, user_context)
    save_trace(trace, run_id)

    # 第 2 层: 确定性检查
    det_report = grade(trace)
    det_result = {
        "all_passed": det_report.all_passed,
        "hard_fail": det_report.hard_fail,
        "pass_rate": det_report.pass_rate,
        "failed_checks": [
            f"[{c.severity}] {c.rule_name}: {c.detail}"
            for c in det_report.checks if not c.passed
        ],
    }

    result = {
        "case_id": case["id"],
        "case_name": case["name"],
        "deterministic": det_result,
        "efficiency": {
            "tool_call_count": len(trace.tool_calls),
            "token_usage": trace.token_usage,
            "agent_loop_rounds": trace.agent_loop_rounds,
        },
    }

    # 第 3 层: LLM Judge（确定性硬性失败时跳过，省钱）
    if not deterministic_only and not det_report.hard_fail:
        llm_result = await call_llm_judge(case, trace)
        result["llm_judge"] = llm_result

    return result


async def main():
    parser = argparse.ArgumentParser(description="Isho Agent Eval Runner")
    parser.add_argument("--profile", type=str, help="只运行指定画像 (A/B/C/D)")
    parser.add_argument("--case", nargs="+", help="只运行指定 case (如 A01 A03)")
    parser.add_argument("--deterministic-only", action="store_true",
                        help="只跑确定性检查，跳过 LLM Judge")
    args = parser.parse_args()

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    profiles = load_profiles(args.profile)

    if not profiles:
        print("未找到匹配的画像文件")
        sys.exit(1)

    all_results = []
    for profile in profiles:
        print(f"\n{'='*60}")
        print(f"画像: {profile['profile_name']}")
        print(f"{'='*60}")

        # 加载 user context
        ctx_path = EVAL_DIR / profile["user_context_file"]
        user_context = ctx_path.read_text(encoding="utf-8") if ctx_path.exists() else ""

        for case in profile["cases"]:
            if args.case and case["id"] not in args.case:
                continue

            print(f"  ▶ {case['id']} {case['name']}...", end=" ", flush=True)
            start = time.time()

            try:
                result = await run_case(
                    case, user_context, run_id,
                    deterministic_only=args.deterministic_only,
                )
                elapsed = time.time() - start
                status = "✅" if result["deterministic"]["all_passed"] else "❌"
                overall = result.get("llm_judge", {}).get("overall_score", "-")
                print(f"{status} det={result['deterministic']['pass_rate']} llm={overall} ({elapsed:.1f}s)")
            except NotImplementedError as e:
                print(f"⏭️  跳过 ({e})")
                continue
            except Exception as e:
                print(f"💥 错误: {e}")
                result = {
                    "case_id": case["id"],
                    "case_name": case["name"],
                    "deterministic": {"all_passed": False, "hard_fail": True, "pass_rate": "0/0", "failed_checks": [str(e)]},
                    "error": str(e),
                }

            all_results.append(result)

    if all_results:
        generate_report(all_results, run_id)


if __name__ == "__main__":
    asyncio.run(main())
