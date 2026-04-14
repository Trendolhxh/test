"""
生成完整评测 CSV — 包含 输入/过程/输出/评价 四组列。

每行 = 一轮 user-agent 交互（多轮 case 展开为多行）。

用法:
    python generate_full_csv.py                     # 使用最新 report
    python generate_full_csv.py --run-id 20260410_143200
"""

import argparse
import csv
import json
import re
from pathlib import Path

# ── 路径 ──────────────────────────────────────────────────

EVAL_DIR = Path(__file__).parent
PROFILE_FILES = sorted(EVAL_DIR.glob("profile-*.json"))
USER_CTX_DIR = EVAL_DIR / "user-contexts"
REPORT_DIR = EVAL_DIR / "reports"
TRACE_DIR = EVAL_DIR / "traces"
RULES_PATH = EVAL_DIR / "graders" / "rules.json"

# ── CSV 列定义（30 列）────────────────────────────────────

CSV_COLUMNS = [
    # 第 1 组: 输入 (Input)
    "profile_id",
    "profile_name",
    "case_id",
    "case_name",
    "turn_index",
    "event_type",
    "event_timestamp",
    "user_context_summary",
    "scene_instruction",
    "user_message",
    # 第 2 组: 过程 (Process)
    "agent_loop_rounds",
    "tool_call_count",
    "tool_calls_detail",
    "turn_input_tokens",       # 预留
    "turn_output_tokens",      # 预留
    "turn_duration_ms",        # 预留
    "per_step_durations",      # 预留
    # 第 3 组: 输出 (Output)
    "response_text",
    # 第 4 组: 评价 (Evaluation)
    # 4a. Guideline
    "expected_tool_calls",
    "expected_response",
    "rules_applied",
    # 4b. Guideline 满足情况
    "det_pass_rate",
    "det_all_passed",
    "det_hard_fail",
    "det_failed_checks",
    "total_token_usage",
    "total_duration_ms",       # 预留
    # 4c. 主观评价 (PM 自定义)
    "subjective_score",
    "subjective_note",
    "subjective_raw",
]


# ── 数据加载 ──────────────────────────────────────────────

def load_profiles() -> list[dict]:
    """加载全部 profile JSON，返回列表。"""
    profiles = []
    for p in PROFILE_FILES:
        profiles.append(json.loads(p.read_text(encoding="utf-8")))
    return profiles


def load_user_context_summaries(profiles: list[dict]) -> dict[str, str]:
    """从 YAML 中提取每个画像的 [summary] 行。返回 {profile_id: summary_text}。"""
    summaries = {}
    for profile in profiles:
        ctx_path = EVAL_DIR / profile["user_context_file"]
        if not ctx_path.exists():
            summaries[profile["profile_id"]] = ""
            continue
        text = ctx_path.read_text(encoding="utf-8")
        # 提取 # [summary] 后面到下一个 # [ 之间的文本
        match = re.search(r"#\s*\[summary\]\s*\n(.+?)(?=\n#\s*\[|\Z)", text, re.DOTALL)
        summaries[profile["profile_id"]] = match.group(1).strip() if match else ""
    return summaries


def load_report(run_id: str) -> dict:
    """加载指定 run_id 的 JSON 报告。"""
    path = REPORT_DIR / f"{run_id}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_traces(run_id: str) -> dict[str, dict]:
    """加载 traces 目录下匹配 run_id 的所有 trace。返回 {case_id: trace_dict}。"""
    traces = {}
    for f in TRACE_DIR.glob(f"{run_id}_*.json"):
        data = json.loads(f.read_text(encoding="utf-8"))
        traces[data["case_id"]] = data
    return traces


def load_rules() -> dict:
    """加载确定性规则。"""
    return json.loads(RULES_PATH.read_text(encoding="utf-8"))


# ── 格式化函数 ────────────────────────────────────────────

def format_tool_calls_detail(tool_calls: list[dict]) -> str:
    """将 tool_calls 列表格式化为箭头链字符串。

    输入: [{"name": "get_strategy", "arguments": {"aspects": ["action"]}}]
    输出: 'get_strategy({aspects:["action"]})'
    """
    if not tool_calls:
        return ""
    parts = []
    for tc in tool_calls:
        name = tc["name"]
        args = tc.get("arguments", {})
        # 紧凑 JSON：去掉多余空格
        args_str = json.dumps(args, ensure_ascii=False, separators=(",", ":"))
        parts.append(f"{name}({args_str})")
    return " → ".join(parts)


def format_rules_applied(case_id: str, rules: dict) -> str:
    """构建该 case 适用的规则摘要字符串。"""
    parts = []

    # 全局规则
    global_rules = rules.get("global_rules", {})
    global_parts = []
    bl = global_rules.get("blacklist_phrases", {})
    if bl:
        global_parts.append(f"blacklist({len(bl.get('phrases', []))}词)")
    fmt = global_rules.get("no_markdown_formatting", {})
    if fmt:
        global_parts.append(f"no_markdown({len(fmt.get('patterns', []))}式)")
    if global_parts:
        parts.append("全局:" + "+".join(global_parts))

    # case 专属规则
    case_rules = rules.get("case_rules", {}).get(case_id, {})
    if case_rules:
        case_parts = []
        if "tool_calls_required" in case_rules:
            tools = ",".join(case_rules["tool_calls_required"])
            case_parts.append(f"tool_required({tools})")
        if "tool_calls_forbidden" in case_rules:
            tools = ",".join(case_rules["tool_calls_forbidden"])
            case_parts.append(f"tool_forbidden({tools})")
        if "response_blacklist" in case_rules:
            case_parts.append(f"blacklist({len(case_rules['response_blacklist'])}词)")
        if "response_blacklist_refs" in case_rules:
            refs = ",".join(case_rules["response_blacklist_refs"])
            case_parts.append(f"blacklist_refs({refs})")
        if "response_max_sentences" in case_rules:
            case_parts.append(f"max_sentences({case_rules['response_max_sentences']})")
        if case_rules.get("response_must_not_be_list"):
            case_parts.append("must_not_be_list")
        if case_parts:
            severity = case_rules.get("severity_override", "")
            case_str = "case:" + "+".join(case_parts)
            if severity:
                case_str += f" | severity:{severity}"
            parts.append(case_str)

    return " | ".join(parts)


def extract_user_messages_as_turns(messages: list[dict]) -> list[str]:
    """从 messages 数组中提取每轮用户消息。

    当前 case 都是单轮（一条 user message），未来多轮 case
    会有 user/assistant 交替的 messages。按 user 消息分轮。
    """
    if not messages:
        return [""]  # 非用户发起的场景（app_open 等），仍保留一行

    user_turns = []
    for msg in messages:
        if msg.get("role") == "user":
            user_turns.append(msg.get("content", ""))

    return user_turns if user_turns else [""]


# ── 构建 CSV 行 ──────────────────────────────────────────

def build_rows(profiles, summaries, report, traces, rules) -> list[dict]:
    """构建所有 CSV 行。"""
    # 将 report results 索引化
    report_by_case = {r["case_id"]: r for r in report.get("results", [])}

    rows = []
    for profile in profiles:
        pid = profile["profile_id"]
        pname = profile["profile_name"]
        summary = summaries.get(pid, "")

        for case in profile["cases"]:
            cid = case["id"]
            cname = case["name"]
            evt = case.get("event_context", {})
            scene = case.get("scene_instruction") or ""
            trace = traces.get(cid)
            result = report_by_case.get(cid, {})

            # 拆分为 turn 行
            user_turns = extract_user_messages_as_turns(case.get("messages", []))
            total_turns = len(user_turns)

            for i, user_msg in enumerate(user_turns):
                turn_idx = i + 1
                is_last_turn = (turn_idx == total_turns)

                row = {col: "" for col in CSV_COLUMNS}

                # ── 第 1 组: 输入 ──
                row["profile_id"] = pid
                row["profile_name"] = pname
                row["case_id"] = cid
                row["case_name"] = cname
                row["turn_index"] = turn_idx
                row["event_type"] = evt.get("event_type", "")
                row["event_timestamp"] = evt.get("timestamp", "")
                row["user_context_summary"] = summary
                row["scene_instruction"] = scene
                row["user_message"] = user_msg

                # ── 第 2 组: 过程（仅有 trace 时填充）──
                if trace and is_last_turn:
                    # 当前 trace 是整个 case 级别的，放在最后一轮
                    row["agent_loop_rounds"] = trace.get("agent_loop_rounds", "")
                    row["tool_call_count"] = len(trace.get("tool_calls", []))
                    row["tool_calls_detail"] = format_tool_calls_detail(
                        trace.get("tool_calls", [])
                    )
                elif not trace and is_last_turn:
                    # 无 trace 但 report 中有汇总数据
                    eff = result.get("efficiency", {})
                    if eff:
                        row["agent_loop_rounds"] = eff.get("agent_loop_rounds", "")
                        row["tool_call_count"] = eff.get("tool_call_count", "")
                # 预留列保持为空

                # ── 第 3 组: 输出 ──
                if trace and is_last_turn:
                    row["response_text"] = trace.get("response_text", "")

                # ── 第 4 组: 评价（仅最后一轮填充）──
                if is_last_turn:
                    # 4a. Guideline
                    row["expected_tool_calls"] = case.get("expected_tool_calls", "")
                    row["expected_response"] = case.get("expected_response", "")
                    row["rules_applied"] = format_rules_applied(cid, rules)

                    # 4b. Guideline 满足情况
                    det = result.get("deterministic", {})
                    row["det_pass_rate"] = det.get("pass_rate", "")
                    row["det_all_passed"] = det.get("all_passed", "")
                    row["det_hard_fail"] = det.get("hard_fail", "")
                    row["det_failed_checks"] = "; ".join(
                        det.get("failed_checks", [])
                    )
                    row["total_token_usage"] = result.get("efficiency", {}).get(
                        "token_usage", ""
                    )
                    # total_duration_ms 预留

                    # 4c. 主观评价 — 预留为空

                rows.append(row)

    return rows


# ── 写 CSV ────────────────────────────────────────────────

def write_csv(rows: list[dict], output_path: Path):
    """写入 UTF-8 with BOM 的 CSV 文件。"""
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


# ── 主入口 ────────────────────────────────────────────────

def find_latest_run_id() -> str:
    """从 reports/ 目录找到最新的 run_id。"""
    json_files = sorted(REPORT_DIR.glob("*.json"))
    if not json_files:
        raise FileNotFoundError("reports/ 目录下没有 JSON 报告")
    # 取文件名（不含后缀）作为 run_id
    return json_files[-1].stem


def main():
    parser = argparse.ArgumentParser(description="生成完整评测 CSV")
    parser.add_argument("--run-id", type=str, help="指定 run_id（默认使用最新）")
    args = parser.parse_args()

    run_id = args.run_id or find_latest_run_id()
    print(f"Run ID: {run_id}")

    # 加载数据
    print("加载 profiles...", end=" ")
    profiles = load_profiles()
    print(f"{len(profiles)} 个画像")

    print("加载 user context summaries...", end=" ")
    summaries = load_user_context_summaries(profiles)
    print(f"{len(summaries)} 个")

    print("加载 report...", end=" ")
    report = load_report(run_id)
    print(f"{len(report.get('results', []))} 条结果")

    print("加载 traces...", end=" ")
    traces = load_traces(run_id)
    print(f"{len(traces)} 条 trace")

    print("加载 rules...", end=" ")
    rules = load_rules()
    case_rule_count = len(rules.get("case_rules", {}))
    print(f"全局 + {case_rule_count} 条 case 规则")

    # 构建行
    rows = build_rows(profiles, summaries, report, traces, rules)
    print(f"\n生成 {len(rows)} 行 CSV（{len(CSV_COLUMNS)} 列）")

    # 写文件
    output_path = REPORT_DIR / f"{run_id}_full.csv"
    write_csv(rows, output_path)
    print(f"已保存: {output_path}")

    # 统计
    has_trace = sum(1 for r in rows if r["tool_calls_detail"])
    has_response = sum(1 for r in rows if r["response_text"])
    print(f"\n统计:")
    print(f"  有 tool_calls_detail 的行: {has_trace}/{len(rows)}")
    print(f"  有 response_text 的行: {has_response}/{len(rows)}")
    reserved = ["turn_input_tokens", "turn_output_tokens", "turn_duration_ms",
                 "per_step_durations", "total_duration_ms",
                 "subjective_score", "subjective_note", "subjective_raw"]
    print(f"  预留列（当前为空）: {', '.join(reserved)}")


if __name__ == "__main__":
    main()
