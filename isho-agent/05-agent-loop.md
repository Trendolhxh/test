# 05 - Agent 循环

> 模型推理 → 工具调用 → 观察结果 → 继续/停止

---

## 精力管家的循环特点

精力管家不是 Claude Code。Claude Code 是重工具型 agent（读文件→改代码→跑测试→循环多轮），精力管家是**轻工具型、重对话型**——大部分价值在对话本身，工具调用少且轻。

V3 记忆架构下，模型可能在首轮调用 `get_user_profile` / `get_strategy` 拉取用户上下文，但这仍然是"查→用"的简单模式。

典型对话中工具调用模式：
- 纯闲聊 → 直接回复（0 次工具调用，速览已够用）
- 查数据 → 回复用户（1 次 get_health_data）
- 聊天中捕获信息 → 记下来（1 次 save_memory）
- 给建议 → 拉策略 + 发反馈卡片（get_strategy + send_feedback_card）
- 做分析 → 拉趋势 + 查数据 + 渲染卡片（get_strategy + get_health_data + render_analysis_card）

**绝大多数轮次只有 0-2 次工具调用，不需要复杂的循环控制。**

---

## 循环流程

```mermaid
flowchart TD
    A["用户消息到达"] --> B["模型推理（第 1 轮）"]
    B -->|"直接回复文本"| END1["结束（最常见路径·纯闲聊）"]
    B -->|"调用工具"| C["执行工具"] --> D["返回结果"]
    D --> E["模型推理（第 2 轮）"]
    E -->|"回复文本"| END2["结束（多数场景在此结束）"]
    E -->|"调用工具"| F["执行工具 → 返回结果"]
    F --> G["模型推理（第 3 轮）"]
    G -->|"回复文本"| END3["结束"]
    G -->|"调用工具"| H["执行工具 → ...（极少到第 4 轮）"]
```

---

## 终止条件

| 条件 | 说明 |
|------|------|
| 模型输出文本（无工具调用） | 正常结束，最常见 |
| 达到最大轮次（4 轮） | 强制终止，要求模型用已有信息回复 |
| 工具执行报错 | 将错误信息返回模型，让模型决定是重试还是向用户说明 |

**最大 4 轮的理由：**
- V3 架构下，模型可能需要先拉上下文（get_user_profile / get_strategy），再查数据（get_health_data），再回复并附带工具（save_memory / suggest_replies），典型路径是 3 轮
- 第 4 轮作为安全余量，覆盖极少数需要额外一轮的场景
- 如果 4 轮还没完成，说明出了问题，不应该让 agent 自己转圈

---

## 常见调用模式

大部分对话属于以下模式之一：

| 模式 | 工具调用次数 | 典型场景 |
|------|:-----------:|---------|
| 纯对话 | 0 | 日常聊天、闲聊（速览已够用） |
| 查数据后回复 | 1-2 | 用户问"最近睡得怎么样"→ get_strategy(["trends"]) + get_health_data |
| 记录 + 回复 | 1 | 用户透露新的生活细节 → save_memory |
| 给建议 + 反馈卡 | 2-3 | get_strategy(["redlines","active"]) + 行动建议 + send_feedback_card |
| 数据分析 + 原生卡片 | 2-3 | get_strategy(["trends"]) + get_health_data + render_analysis_card |
| 反馈卡回收 | 2 | get_strategy(["active"]) + get_user_profile(["sleep_strengths"]) |

每种模式下完整的工具调用链和用户侧体验，详见 [06-output-style.md](./06-output-style.md) 的"工具组合输出"章节。

---

## 并行工具调用

Claude 支持单轮返回多个工具调用。精力管家中的并行场景：

- `get_user_profile` + `get_strategy`：两个工具可并行调用，一次拉取所有需要的上下文
- `save_memory` + `send_feedback_card`：记录反馈的同时安排下一次反馈卡
- `save_memory` + `set_reminder` + `suggest_replies`：给完建议后一次性设置提醒、安排反馈、展示按钮
- `get_health_data` 多指标查询：已通过 metrics 数组在单次调用中解决，不需要并行

不需要特殊处理，使用 Claude API 默认的并行工具调用能力即可。
