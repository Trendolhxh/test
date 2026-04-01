"""
确定性 grader — 在 LLM Judge 之前运行，检查可用规则判断的硬性约束。

输入: 一条 eval trace（包含 tool_calls + response_text）
输出: 每条规则的 pass/fail + 原因
"""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

# ── 数据结构 ──────────────────────────────────────────────

@dataclass
class CheckResult:
    rule_name: str
    passed: bool
    severity: str          # "hard_fail" | "soft_fail"
    detail: str = ""

@dataclass
class TraceRecord:
    """从 agent 运行中提取的结构化 trace。"""
    case_id: str
    tool_calls: list[dict]          # [{"name": "get_strategy", "arguments": {...}}, ...]
    response_text: str
    token_usage: int = 0            # prompt + completion tokens
    agent_loop_rounds: int = 1

@dataclass
class GradeReport:
    case_id: str
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def hard_fail(self) -> bool:
        return any(not c.passed and c.severity == "hard_fail" for c in self.checks)

    @property
    def all_passed(self) -> bool:
        return all(c.passed for c in self.checks)

    @property
    def pass_rate(self) -> str:
        total = len(self.checks)
        passed = sum(1 for c in self.checks if c.passed)
        return f"{passed}/{total}"


# ── 规则加载 ──────────────────────────────────────────────

RULES_PATH = Path(__file__).parent / "rules.json"

def load_rules() -> dict:
    with open(RULES_PATH, encoding="utf-8") as f:
        return json.load(f)


# ── 检查函数 ──────────────────────────────────────────────

def _count_sentences(text: str) -> int:
    """粗略按中文句号/问号/感叹号 + 英文句号分句。"""
    parts = re.split(r"[。！？!?\n]", text)
    return len([p for p in parts if p.strip()])


def check_blacklist_phrases(text: str, phrases: list[str], severity: str) -> list[CheckResult]:
    results = []
    for phrase in phrases:
        found = phrase.lower() in text.lower()
        results.append(CheckResult(
            rule_name=f"blacklist:{phrase}",
            passed=not found,
            severity=severity,
            detail=f"回复中包含禁止短语「{phrase}」" if found else "",
        ))
    return results


def check_blacklist_patterns(text: str, patterns: list[str], severity: str) -> list[CheckResult]:
    results = []
    for pat in patterns:
        match = re.search(pat, text, re.MULTILINE)
        results.append(CheckResult(
            rule_name=f"pattern:{pat}",
            passed=match is None,
            severity=severity,
            detail=f"匹配到禁止格式: {match.group()}" if match else "",
        ))
    return results


def check_tool_calls_required(trace: TraceRecord, required: list[str]) -> list[CheckResult]:
    called = {tc["name"] for tc in trace.tool_calls}
    results = []
    for tool in required:
        found = tool in called
        results.append(CheckResult(
            rule_name=f"tool_required:{tool}",
            passed=found,
            severity="hard_fail",
            detail="" if found else f"未调用必须的工具 {tool}",
        ))
    return results


def check_tool_calls_forbidden(trace: TraceRecord, forbidden: list[str]) -> list[CheckResult]:
    called = {tc["name"] for tc in trace.tool_calls}
    results = []
    for tool in forbidden:
        found = tool in called
        results.append(CheckResult(
            rule_name=f"tool_forbidden:{tool}",
            passed=not found,
            severity="soft_fail",
            detail=f"调用了不应调用的工具 {tool}" if found else "",
        ))
    return results


def check_max_sentences(text: str, max_sentences: int) -> CheckResult:
    count = _count_sentences(text)
    passed = count <= max_sentences
    return CheckResult(
        rule_name=f"max_sentences:{max_sentences}",
        passed=passed,
        severity="soft_fail",
        detail="" if passed else f"回复 {count} 句，超过上限 {max_sentences} 句",
    )


def check_not_list_format(text: str) -> CheckResult:
    """检查回复是否包含列表格式（给了多条建议而非一条）。"""
    list_patterns = [r"^\s*\d+[.、）)]", r"^\s*[-•·]"]
    is_list = any(re.search(p, text, re.MULTILINE) for p in list_patterns)
    return CheckResult(
        rule_name="not_list_format",
        passed=not is_list,
        severity="soft_fail",
        detail="回复使用了列表格式（应只给一条建议）" if is_list else "",
    )


# ── 效率指标 ──────────────────────────────────────────────

def check_efficiency(trace: TraceRecord) -> list[CheckResult]:
    results = []

    # 工具调用次数
    tool_count = len(trace.tool_calls)
    results.append(CheckResult(
        rule_name="efficiency:tool_call_count",
        passed=tool_count <= 8,
        severity="soft_fail",
        detail=f"工具调用 {tool_count} 次" + ("，可能存在循环" if tool_count > 8 else ""),
    ))

    # 重复调用检测
    tool_names = [tc["name"] for tc in trace.tool_calls]
    for name in set(tool_names):
        count = tool_names.count(name)
        if count >= 3:
            results.append(CheckResult(
                rule_name=f"efficiency:repeat:{name}",
                passed=False,
                severity="soft_fail",
                detail=f"工具 {name} 被调用 {count} 次，疑似循环",
            ))

    # agent loop 轮数
    if trace.agent_loop_rounds > 3:
        results.append(CheckResult(
            rule_name="efficiency:loop_rounds",
            passed=False,
            severity="soft_fail",
            detail=f"agent loop 跑了 {trace.agent_loop_rounds} 轮（上限 4）",
        ))

    return results


# ── 主入口 ──────────────────────────────────────────────

def grade(trace: TraceRecord) -> GradeReport:
    """对一条 trace 运行所有确定性检查，返回 GradeReport。"""
    rules = load_rules()
    report = GradeReport(case_id=trace.case_id)

    # 1. 全局规则
    global_rules = rules.get("global_rules", {})

    bl = global_rules.get("blacklist_phrases", {})
    if bl:
        report.checks.extend(
            check_blacklist_phrases(trace.response_text, bl["phrases"], bl["severity"])
        )

    fmt = global_rules.get("no_markdown_formatting", {})
    if fmt:
        report.checks.extend(
            check_blacklist_patterns(trace.response_text, fmt["patterns"], fmt["severity"])
        )

    # 2. case 级规则
    case_rules = rules.get("case_rules", {}).get(trace.case_id, {})
    severity = case_rules.get("severity_override", "hard_fail")

    if "tool_calls_required" in case_rules:
        report.checks.extend(
            check_tool_calls_required(trace, case_rules["tool_calls_required"])
        )

    if "tool_calls_forbidden" in case_rules:
        report.checks.extend(
            check_tool_calls_forbidden(trace, case_rules["tool_calls_forbidden"])
        )

    if "response_blacklist" in case_rules:
        report.checks.extend(
            check_blacklist_phrases(
                trace.response_text,
                case_rules["response_blacklist"],
                severity,
            )
        )

    if "response_max_sentences" in case_rules:
        report.checks.append(
            check_max_sentences(trace.response_text, case_rules["response_max_sentences"])
        )

    if case_rules.get("response_must_not_be_list"):
        report.checks.append(check_not_list_format(trace.response_text))

    # 3. 效率指标
    report.checks.extend(check_efficiency(trace))

    return report
