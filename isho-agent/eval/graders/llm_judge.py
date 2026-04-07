"""
LLM Judge — 用结构化 schema 输出多维度评分，取代单一 0-100 打分。

调用方式:
    score = await judge(case, trace, model="gpt-4o-mini")
"""

import json
import re
from pathlib import Path

# ── 加载外部 Judge Prompt ─────────────────────────────────

def _load_judge_prompt() -> str:
    """从 judge-prompt.md 加载 system prompt（提取 code block 中的纯文本）。"""
    prompt_path = Path(__file__).parent / "judge-prompt.md"
    content = prompt_path.read_text(encoding="utf-8")
    match = re.search(r"```text\n(.*?)```", content, re.DOTALL)
    if match:
        return match.group(1).strip()
    raise FileNotFoundError(f"无法从 {prompt_path} 中提取 prompt 正文")

# ── 输出 Schema（要求 LLM 严格返回此结构）───────────────────

JUDGE_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "outcome": {
            "type": "object",
            "description": "任务目标是否达成（回复内容是否正确、完整）",
            "properties": {
                "pass": {"type": "boolean"},
                "score": {"type": "integer", "minimum": 0, "maximum": 100},
                "note": {"type": "string", "description": "简要说明，1句话"}
            },
            "required": ["pass", "score", "note"]
        },
        "process": {
            "type": "object",
            "description": "过程是否正确（工具调用顺序、参数是否合理）",
            "properties": {
                "pass": {"type": "boolean"},
                "score": {"type": "integer", "minimum": 0, "maximum": 100},
                "note": {"type": "string"}
            },
            "required": ["pass", "score", "note"]
        },
        "style": {
            "type": "object",
            "description": "风格是否符合要求（语气像朋友、不说教、不像AI报告）",
            "properties": {
                "pass": {"type": "boolean"},
                "score": {"type": "integer", "minimum": 0, "maximum": 100},
                "note": {"type": "string"}
            },
            "required": ["pass", "score", "note"]
        },
        "overall_score": {
            "type": "integer",
            "minimum": 0,
            "maximum": 100,
            "description": "综合分数，outcome 权重 50%，process 20%，style 30%"
        }
    },
    "required": ["outcome", "process", "style", "overall_score"],
    "additionalProperties": False
}


# ── Judge Prompt（从外部文件加载）────────────────────────

JUDGE_SYSTEM_PROMPT = _load_judge_prompt()

JUDGE_USER_TEMPLATE = """\
## 用例信息
- case_id: {case_id}
- case_name: {case_name}
- expected_tool_calls: {expected_tool_calls}
- expected_response: {expected_response}

## Agent 实际输出
### Tool Calls
{actual_tool_calls}

### Response Text
{actual_response}
"""


def build_judge_messages(case: dict, trace_tool_calls: list[dict], response_text: str) -> list[dict]:
    """组装发给 LLM Judge 的 messages。"""
    return [
        {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
        {"role": "user", "content": JUDGE_USER_TEMPLATE.format(
            case_id=case["id"],
            case_name=case["name"],
            expected_tool_calls=case.get("expected_tool_calls", "无特殊要求"),
            expected_response=case.get("expected_response", "无特殊要求"),
            actual_tool_calls=json.dumps(trace_tool_calls, ensure_ascii=False, indent=2),
            actual_response=response_text,
        )},
    ]


# ── 示例调用（伪代码，适配你的 API 客户端）──────────────────

async def judge(case: dict, trace_tool_calls: list[dict], response_text: str,
                *, model: str = "gpt-4o-mini", client=None) -> dict:
    """
    调用 LLM Judge，返回结构化评分。

    返回示例:
    {
        "outcome": {"pass": true, "score": 85, "note": "正确关联了手机放客厅干预"},
        "process": {"pass": true, "score": 90, "note": "工具调用合理"},
        "style":   {"pass": false, "score": 55, "note": "语气偏正式，用了'数据显示'"},
        "overall_score": 75
    }
    """
    messages = build_judge_messages(case, trace_tool_calls, response_text)

    # ↓ 替换为你实际使用的 API 客户端
    response = await client.chat.completions.create(
        model=model,
        messages=messages,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "eval_judge_score",
                "strict": True,
                "schema": JUDGE_OUTPUT_SCHEMA,
            }
        },
        temperature=0,
    )

    return json.loads(response.choices[0].message.content)
