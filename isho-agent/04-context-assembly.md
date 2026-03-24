# 04 - 上下文组装

> 每次 API 调用时，system / tools / messages 怎么拼、token 怎么分

---

## 组装结构

```
┌─ system ──────────────────────────────────────────┐
│ ① 身份层（01-system-prompt）             ~200 tk  │
│ ② 用户画像.md（get_user_context 返回）    ~400 tk  │
│ ③ 干预策略.md（get_user_context 返回）    ~400 tk  │
│ ④ 场景指令（07-events 根据触发场景注入）   ~100 tk  │
├─ tools ───────────────────────────────────────────┤
│ ⑤ 7 个工具定义（JSON schema）             ~800 tk  │
├─ messages ────────────────────────────────────────┤
│ ⑥ 对话历史                              剩余空间   │
└───────────────────────────────────────────────────┘
```

### 为什么用户画像和干预策略放在 system 里

- 这两份文档是**每轮都需要的背景知识**，类似 Claude Code 把 CLAUDE.md 注入 system
- 放 system 而非 messages，确保多轮对话中不会被挤出上下文窗口
- 放在身份层之后、工具之前——agent 先知道"我是谁"，再知道"我面对的用户是什么情况"，最后知道"我能用什么工具"

---

## Token 预算

以 Claude Sonnet 200K 上下文为基准，实际对话不会太长（非编程场景），预留 8K 足够：

| 区块 | 预算 | 说明 |
|------|------|------|
| 身份层 | ~200 tk | 固定，不随用户变化 |
| 用户画像.md | ~400 tk | 子 agent 控制篇幅 |
| 干预策略.md | ~400 tk | 子 agent 控制篇幅 |
| 场景指令 | ~100 tk | 按触发场景注入，可能为空 |
| 工具定义 | ~800 tk | 7 个工具的 JSON schema（get_user_context 不在列表中） |
| **system + tools 合计** | **~1900 tk** | |
| 对话历史 | ~4000 tk | 单次会话通常 10-20 轮 |
| 模型输出 | ~2000 tk | 单次回复上限 |
| **总计** | **~7900 tk** | 远低于上下文上限，无压缩需求 |

> 精力管家是短对话场景（用户聊几句就走），不像 Claude Code 动辄几百轮。
> 不需要设计对话压缩策略，如果未来对话变长再考虑。

---

## 组装流程（伪代码）

```python
def assemble_context(user_id, trigger_event, conversation_history):
    # ① 身份层 — 固定
    system_parts = [SYSTEM_PROMPT]

    # ② ③ 用户画像 + 干预策略 — 从缓存或数据库加载
    ctx = get_user_context(user_id)
    system_parts.append(ctx.user_profile)
    system_parts.append(ctx.intervention_plan)

    # ④ 场景指令 — 根据触发事件注入（详见 07-events）
    if trigger_event:
        system_parts.append(get_event_instruction(trigger_event))

    # ⑤ 工具定义 — 固定
    tools = TOOL_DEFINITIONS

    # ⑥ 对话历史
    messages = conversation_history

    return {
        "system": "\n\n".join(system_parts),
        "tools": tools,
        "messages": messages
    }
```

---

## 首次对话（新用户）

新用户没有画像和干预策略，get_user_context 返回空文档：

```json
{
  "user_profile": "# 用户画像\n\n暂无数据，请通过对话了解用户。",
  "intervention_plan": "# 干预策略\n\n暂无干预记录。",
  "updated_at": null
}
```

此时 agent 的行为由 system prompt 原则 2 驱动——"如果你对用户的情况了解不够，先提问"。不需要额外的"新用户引导指令"，agent 自然会进入提问模式。

---

## 注意事项

- **get_user_context 不在工具列表中**：它由 orchestrator 层自动执行，结果注入 system。02-tools 中保留其定义仅供工程团队参考，不发送给模型。
- **场景指令是可选的**：没有特殊触发事件时（如用户主动发消息），④ 为空。
- **两份 md 的更新时机**：md 由子 agent 异步更新，主 agent 在对话中看到的是上次子 agent 运行后的版本。对话中新写入 mem0 的事实，要到下次子 agent 运行后才反映在 md 中。
