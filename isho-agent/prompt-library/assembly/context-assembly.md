# 上下文组装规范

> 面向工程团队：每次 API 调用时 system / tools / messages 怎么拼

## 组装结构

```
┌─ system prompt ──────────────────────────────────────────────┐
│ ① 身份层         system/01-identity.md           ~250 tk 固定 │
│ ② 用户速览       system/02-user-summary-template   ~80 tk 动态 │
│ ③ 样式指令       system/03-style.md               ~200 tk 固定 │
│ ④ 工具使用总则   system/04-tool-usage-guidelines   ~300 tk 固定 │
│ ⑤ 场景指令       system/scenes/*.md            ~80 tk 动态可选 │
└──────────────────────────────────────────────────────────────┘
┌─ tools ──────────────────────────────────────────────────────┐
│ ⑥ 工具定义       tools/**/*.json              ~1500 tk 按白名单│
└──────────────────────────────────────────────────────────────┘
┌─ messages ───────────────────────────────────────────────────┐
│ ⑦ 对话历史 + 工具调用结果                      剩余空间 动态  │
└──────────────────────────────────────────────────────────────┘
```

## 拼接顺序设计理由

模型对 system prompt **开头和结尾**的内容关注度最高：

1. **身份层最前** — agent 首先知道"我是谁、核心原则是什么"
2. **速览紧随其后** — agent 接着知道"面对的用户基本情况、红线、沟通风格"
3. **样式指令和工具总则在中间** — 约束输出行为和工具使用
4. **场景指令放最后** — 离对话历史最近，和当前上下文关联最强

## 组装伪代码

```python
# ── 固定部分（启动时加载一次）──

IDENTITY = load_file("system/01-identity.md")          # ① 提取 code block 中的纯文本
STYLE = load_file("system/03-style.md")                # ③
TOOL_GUIDELINES = load_file("system/04-tool-usage-guidelines.md")  # ④
TOOL_DEFINITIONS = load_tools_by_allowlist(skill_name)  # ⑥ 按技能白名单加载

# ── 每次 API 调用时组装 ──

def assemble_context(user_id, trigger_event, conversation_history):
    system_parts = []

    # ① 身份层 — 固定
    system_parts.append(IDENTITY)

    # ② 用户速览 — 从数据库加载 [summary] section
    user_summary = db.get_user_summary(user_id)  # ~80 tk
    system_parts.append(user_summary)

    # ③ 样式指令 — 固定
    system_parts.append(STYLE)

    # ④ 工具使用总则 — 固定
    system_parts.append(TOOL_GUIDELINES)

    # ⑤ 场景指令 — 根据触发事件注入
    if trigger_event and trigger_event.scene_data:
        scene_template = load_scene(trigger_event.scene_type)
        system_parts.append(render_template(scene_template, trigger_event.scene_data))

    return {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 2048,
        "system": "\n\n".join(system_parts),     # ①②③④⑤ 拼接
        "tools": TOOL_DEFINITIONS,                # ⑥
        "messages": conversation_history,         # ⑦
    }
```

## 各场景下的组装差异

| 场景 | ①身份 | ②速览 | ③样式 | ④工具总则 | ⑤场景指令 | 对话历史 |
|------|:-----:|:-----:|:-----:|:---------:|:---------:|:-------:|
| 用户主动发消息 | ✅ | ✅ | ✅ | ✅ | 空 | 携带 |
| 反馈卡提交 | ✅ | ✅ | ✅ | ✅ | feedback-submit | 携带 |
| 提醒推送被点击 | ✅ | ✅ | ✅ | ✅ | push-click | 空（新对话）|
| 子 agent 洞察 | ✅ | ✅ | ✅ | ✅ | agent-insight | 空（新对话）|
| 新睡眠数据 | ✅ | ✅ | ✅ | ✅ | new-sleep-data | 空（新对话）|
| 新用户首次对话 | ✅ | 空模板 | ✅ | ✅ | 空 | 空 |

## Agent 循环

```python
MAX_TURNS = 4

for turn in range(MAX_TURNS):
    response = claude_api.create_message(**request)
    tool_calls = extract_tool_calls(response)

    if not tool_calls:
        break  # 纯文本回复 → 循环结束

    tool_results = []
    for call in tool_calls:
        result = execute_tool(call)  # 路由见 tool-routing.md
        tool_results.append(result)

    request["messages"].append({"role": "assistant", "content": response.content})
    request["messages"].append({"role": "user", "content": tool_results})

else:
    # 达到最大轮次，强制要求模型用已有信息回复
    request["messages"].append({
        "role": "user",
        "content": "请用已有信息直接回复用户。"
    })
    response = claude_api.create_message(**request)
```

## 响应投递

```python
delivery = {
    "text": response.text_content,
    "tool_outputs": collect_frontend_outputs(),
}

# 前端按以下顺序渲染：
# 1. show_status（如果有）→ 先显示加载态
# 2. text → 替换加载态，展示文本
# 3. render_health_chart（如果有）→ 文本下方展示图表
# 4. suggest_action_card（如果有）→ 展示决策卡片
# 5. send_feedback_card（如果有）→ 存入待展示队列，到 scheduled_after 再展示
# 6. suggest_replies（如果有）→ 文本/卡片下方展示按钮
# 7. set_reminder → 静默注册到系统推送，不在当前界面展示
```
