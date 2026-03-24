# 07 - 动态事件注入

> 不是所有对话都由用户发消息触发。定义 agent 在什么时机、以什么方式"主动开口"。

---

## 核心问题

agent 需要在特定时机主动说话——用户打开 App 但没发消息、反馈卡提交了、子 agent 发现了异常。这些时机通过**事件**驱动，事件的内容作为**场景指令**注入 04-context-assembly 的第 ④ 块。

---

## 事件类型

### 事件 1：用户主动发消息

最常见的触发方式。不需要场景指令，走标准对话流程。

```
触发条件: 用户在对话框输入并发送了消息
场景指令: 无（不注入额外指令）
agent 行为: 正常响应
```

### 事件 2：用户打开 App（无消息）

用户打开了 App 但没说话。agent 根据当前是否有值得说的事情决定是否主动发言。

```
触发条件: 用户打开 App，进入对话页面，且距离上次对话 > 30 分钟
场景指令: 根据待处理事项注入（见下方优先级）
agent 行为: 如果有场景指令，主动发言；如果没有，保持沉默
```

**沉默条件（不触发 agent）：**
- 距离上次对话 ≤ 30 分钟，且没有新的待处理事项
- 上次对话是 agent 主动发言，用户没有回复就离开了（不要追着说）

### 事件 3：反馈卡提交

用户在反馈卡片上点击了选项并提交。

```
触发条件: 用户提交了 send_feedback_card 的结果
场景指令: 注入反馈内容
agent 行为: 基于反馈推进对话（肯定/调整/追问）
```

### 事件 4：提醒推送被点击

用户点击了 set_reminder 产生的推送通知，进入 App。

```
触发条件: 用户点击推送通知进入 App
场景指令: 注入提醒上下文
agent 行为: 顺着提醒的内容接话
```

### 事件 5：子 agent 发现异常

子 agent（每天 05:00 运行）更新画像/策略时，发现了值得主动提及的变化。

```
触发条件: 子 agent 标记了一条"待推送洞察"
场景指令: 在下次用户打开 App 时注入
agent 行为: 主动分享发现
```

---

## 事件优先级

用户打开 App 时可能同时存在多个待处理事项。不能全塞给 agent——同时处理多件事会让输出混乱。

**优先级排序（高到低）：**

```
1. 用户主动发消息          ← 用户有明确意图，最高优先
2. 提醒推送被点击          ← 用户从推送入口进来，意图明确
3. 子 agent 发现异常       ← 我们发现了值得说的事
4. 反馈卡待收集            ← 之前建议的反馈，最不紧急
```

**规则：**
- 每次只注入一个场景指令，按优先级取最高的
- 被跳过的低优先级事项保留，下次触发时再处理
- 如果用户主动发消息（优先级 1），其他事项全部延后——用户想聊什么就聊什么

**为什么反馈卡收集优先级最低：**

反馈卡有 scheduled_after 控制展示时机，本身就是"不着急"的。而且如果 agent 一开口就问"昨晚那个建议你做到了吗？"，用户会觉得被追责。不如等用户自己提交反馈卡，或者在自然对话中顺便聊到。

---

## 场景指令模板

每个事件对应一段短文本，注入 system prompt 末尾（04-context-assembly 的第 ④ 块）。

### 打开 App + 有新数据

```
## 当前场景

用户刚打开 App。以下是他最新的睡眠数据摘要：
{sleep_summary}

如果数据中有值得关注的变化（好的或坏的），主动和用户聊聊。
如果没什么特别的，简短打个招呼或保持沉默。
不要像报告一样列数据，像朋友一样聊。
```

### 反馈卡提交

```
## 当前场景

用户刚提交了一张反馈卡：
- 关联建议：{suggestion_description}
- 用户选择：{completion_value}
- 用户补充：{follow_up_text}

基于反馈推进对话：
- 做到了 → 肯定 + 考虑是否固化或推进
- 没做到 → 理解原因 + 考虑调整方法
- 部分做到 → 肯定已做到的部分 + 了解困难点
```

### 提醒推送被点击

```
## 当前场景

用户点击了一条提醒推送进入 App：
- 提醒内容：{reminder_message}
- 提醒时间：{reminder_time}
- 关联干预：{intervention_description}

用户可能想聊聊这个提醒，也可能只是顺手点进来。
不要假设用户一定想讨论提醒内容——如果用户另有话题，跟随用户。
```

### 子 agent 发现异常

```
## 当前场景

系统检测到以下值得关注的变化：
{insight_description}

在合适的时机和用户聊聊这个发现。
如果用户主动聊了其他话题，可以在话题自然结束后再提。
不要用"系统检测到"这种话，用你自己的话说。
```

---

## 沉默机制

agent 不应该每次用户打开 App 都说话。**没有值得说的事，就不说。**

### 判断流程

```
用户打开 App
    │
    ├─ 距离上次对话 ≤ 30 分钟？
    │       │
    │       ├─ 有新的待处理事项？ ─→ 注入场景指令，agent 发言
    │       │
    │       └─ 没有 ─→ 沉默（不调用 agent）
    │
    ├─ 距离上次对话 > 30 分钟？
    │       │
    │       ├─ 有待处理事项？ ─→ 注入场景指令，agent 发言
    │       │
    │       └─ 有新睡眠数据（如早上首次打开）？ ─→ 注入数据摘要，agent 可选发言
    │       │
    │       └─ 都没有 ─→ 沉默
    │
    └─ 上次是 agent 主动发言，用户未回复就离开？
            │
            └─ 沉默（不追着说）
```

### "有值得说的事"的定义

| 条件 | 示例 | 是否发言 |
|------|------|---------|
| 有待收集的反馈 | 昨晚的建议到了反馈时间 | 不主动开口，等用户提交卡片 |
| 有新的睡眠数据 | 早上首次打开，昨晚数据已同步 | 可以聊（注入数据摘要） |
| 子 agent 标记了异常 | 连续 3 天深睡下降 | 应该聊（注入异常发现） |
| 用户点了提醒推送进来 | 22:30 的放手机提醒 | 应该聊（注入提醒上下文） |
| 用户几分钟前刚聊过，又打开了 | 没有新事项 | 沉默 |

---

## 注入时序

事件注入发生在 04-context-assembly 的组装阶段，在调用 Claude API 之前。

```python
def handle_app_open(user_id, entry_point):
    """用户打开 App 时的事件处理"""

    # 1. 检查沉默条件
    last_conversation = get_last_conversation(user_id)
    if should_stay_silent(last_conversation, entry_point):
        return None  # 不调用 agent

    # 2. 收集待处理事项，按优先级排序
    pending_events = []

    if entry_point == "push_notification":
        reminder = get_clicked_reminder(user_id)
        pending_events.append(("reminder_clicked", reminder))

    insight = get_pending_insight(user_id)
    if insight:
        pending_events.append(("agent_insight", insight))

    pending_feedback = get_pending_feedback(user_id)
    if pending_feedback:
        pending_events.append(("feedback_pending", pending_feedback))

    # 如果没有待处理事项，检查是否有新数据可聊
    if not pending_events:
        sleep_data = get_latest_sleep_summary(user_id)
        if sleep_data and sleep_data.is_new:
            pending_events.append(("new_sleep_data", sleep_data))

    if not pending_events:
        return None  # 没什么好说的，沉默

    # 3. 取最高优先级事件，生成场景指令
    event_type, event_data = pending_events[0]
    scene_instruction = render_scene_instruction(event_type, event_data)

    # 4. 组装上下文并调用 agent
    context = assemble_context(
        user_id=user_id,
        trigger_event=scene_instruction,
        conversation_history=[]  # agent 主动发言，无用户消息
    )
    return call_agent(context)


def handle_feedback_submit(user_id, feedback_result):
    """用户提交反馈卡时的事件处理"""

    scene_instruction = render_scene_instruction("feedback_submitted", feedback_result)

    context = assemble_context(
        user_id=user_id,
        trigger_event=scene_instruction,
        conversation_history=get_conversation_history(user_id)
    )
    return call_agent(context)
```

---

## 设计说明

| 设计决策 | 理由 |
|---------|------|
| 每次只注入一个场景指令 | 多个指令会让 agent 输出混乱，试图一次处理太多事情 |
| 反馈卡收集优先级最低 | 避免"追责感"，反馈卡本身有延迟展示机制 |
| 沉默是默认状态 | 宁可不说，也不要硬凑一句"早上好"式的废话 |
| 30 分钟冷却期 | 短时间内反复打开 App 是正常使用行为，不应每次都被 agent 搭话 |
| 场景指令是建议不是命令 | 模板中用"如果...可以..."而非"你必须..."，给 agent 判断空间 |
| 子 agent 异常高于反馈收集 | 我们发现的问题比回收历史建议更有时效性 |
