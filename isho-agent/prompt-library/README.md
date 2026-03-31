# 精力管家 Prompt Library

> 仿照 [Claude Code 提示词架构](../claude-code-prompt-architecture.md) 构建的模块化提示词库。
> 每个文件是一个可独立加载的提示词片段，由 orchestrator 在运行时按需拼接。

## 架构概览

```
用户事件到达
    ↓
状态机判定（INVOKE / SILENT）
    ↓
┌─ system prompt（~910 tk）─────────────────────┐
│  01-identity     身份 + 原则 + 认知纪律 + 安全边界 │
│  02-user-summary 用户速览（动态）                 │
│  03-style        输出样式 + 工具配合 + 禁止模式    │
│  04-tool-usage   工具调用总则 + 场景映射           │
│  scenes/*        场景指令（按事件类型动态注入）      │
└──────────────────────────────────────────────┘
┌─ tools（~1,500 tk）──────────────────────────┐
│  13 个 Model-Facing 工具定义（JSON Schema）     │
│  orchestrator 路由到 18+ 个 Server-Side RPC    │
└──────────────────────────────────────────────┘
┌─ messages ───────────────────────────────────┐
│  对话历史 + 工具调用结果                        │
└──────────────────────────────────────────────┘
```

## 目录结构

### system/ — System Prompt 片段

注入 API 的 `system` 字段，按固定顺序拼接。

| 文件 | 内容 | token | 加载方式 |
|------|------|-------|---------|
| [01-identity.md](system/01-identity.md) | 身份声明、核心原则、认知纪律、安全边界 | ~250 | 固定 |
| [02-user-summary-template.md](system/02-user-summary-template.md) | 用户速览模板（含新用户空模板） | ~80 | 按用户动态 |
| [03-style.md](system/03-style.md) | 说话方式、工具配合规则、禁止模式 | ~200 | 固定 |
| [04-tool-usage-guidelines.md](system/04-tool-usage-guidelines.md) | 工具调用总则、错误处理、场景→工具映射 | ~300 | 固定 |

### system/principles/ — 原则原子文件

从 01-identity.md 拆出的独立原则片段，可按需单独加载或组合。

| 文件 | 内容 |
|------|------|
| [goal-alignment.md](system/principles/goal-alignment.md) | 核心原则 #1：目标对齐（所有建议指向睡眠质量）|
| [reality-first.md](system/principles/reality-first.md) | 核心原则 #2：从真实生活出发 |
| [continuous-learning.md](system/principles/continuous-learning.md) | 核心原则 #3：持续了解用户 |
| [actionable-advice.md](system/principles/actionable-advice.md) | 核心原则 #4：可执行可反馈 |

### system/cognition/ — 认知纪律

| 文件 | 内容 |
|------|------|
| [data-discipline.md](system/cognition/data-discipline.md) | 数据使用纪律（先查后说、关注异常值、坦诚不确定性）|

### system/boundaries/ — 安全边界

| 文件 | 内容 |
|------|------|
| [medical-safety.md](system/boundaries/medical-safety.md) | 医疗安全（不诊断、不处方、红线不触碰、不编造数据）|

### system/doing-tasks/ — 行为规则（"做事原则"）

仿照 Claude Code 的 "Doing Tasks" 模式，每个文件一条原子规则。

| 文件 | 规则 |
|------|------|
| [one-action-not-five.md](system/doing-tasks/one-action-not-five.md) | 一次只给一个建议，不列清单 |
| [check-before-advise.md](system/doing-tasks/check-before-advise.md) | 给建议前必须先查 get_strategy |
| [no-lecturing.md](system/doing-tasks/no-lecturing.md) | 不说教，用引导代替教育 |
| [progress-over-perfection.md](system/doing-tasks/progress-over-perfection.md) | 进步优先于完美 |
| [close-the-loop.md](system/doing-tasks/close-the-loop.md) | 建议→提醒→反馈完整闭环 |

### system/reminders/ — 系统提醒

运行时动态注入的提醒，可叠加。仿照 Claude Code 的 37+ system-reminders 模式。

| 文件 | 触发条件 |
|------|---------|
| [new-user.md](system/reminders/new-user.md) | 新用户首次对话 |
| [user-inactive.md](system/reminders/user-inactive.md) | 用户 3+ 天未活跃 |
| [sleep-anomaly.md](system/reminders/sleep-anomaly.md) | 连续 2+ 天睡眠异常 |
| [streak-status.md](system/reminders/streak-status.md) | 干预执行连续成功/失败 |
| [time-of-day.md](system/reminders/time-of-day.md) | 每次对话根据当前时间注入 |
| [intervention-milestone.md](system/reminders/intervention-milestone.md) | 干预达到时间/数据里程碑 |
| [tool-error-consecutive.md](system/reminders/tool-error-consecutive.md) | 连续 2 个工具调用失败 |

### system/scenes/ — 场景指令模板

当特定事件触发 agent 时，注入 system prompt 末尾。变量由 orchestrator 填充。

| 文件 | 触发条件 | token |
|------|---------|-------|
| [feedback-submit.md](system/scenes/feedback-submit.md) | 用户提交反馈卡 | ~80 |
| [push-click.md](system/scenes/push-click.md) | 用户点击推送提醒 | ~60 |
| [agent-insight.md](system/scenes/agent-insight.md) | 子 agent 标记了待推送洞察 | ~50 |
| [new-sleep-data.md](system/scenes/new-sleep-data.md) | 新睡眠数据到达 + 用户今天首次打开 | ~80 |

用户主动发消息时不注入场景指令。

### tools/ — Model-Facing 工具定义

注入 API 的 `tools` 字段。JSON Schema 格式，`description` 是写给模型看的使用手册。

#### tools/health/ — 健康数据

| 文件 | Model Tool | 背后的 Server Functions |
|------|-----------|----------------------|
| [get_health_data.json](tools/health/get_health_data.json) | `get_health_data` | `get_sleep_data`, `get_hrv_data`, `get_heart_rate`, `get_blood_oxygen`, `get_activity`, `get_workouts`, `get_daily_health_metrics` |

#### tools/memory/ — 记忆系统

| 文件 | Model Tool | 说明 |
|------|-----------|------|
| [get_user_profile.json](tools/memory/get_user_profile.json) | `get_user_profile` | 按需拉取用户画像 sections |
| [get_strategy.json](tools/memory/get_strategy.json) | `get_strategy` | 按需拉取干预策略 sections |
| [save_memory.json](tools/memory/save_memory.json) | `save_memory` | 写入 mem0 事实层 |

#### tools/events/ — 事件记录

| 文件 | Model Tool | 说明 |
|------|-----------|------|
| [record_event.json](tools/events/record_event.json) | `record_event` | 记录行为事件（饮食/运动/小睡/吸烟）|

#### tools/analysis/ — 分析

| 文件 | Model Tool | 说明 |
|------|-----------|------|
| [analyze_food_sleep_impact.json](tools/analysis/analyze_food_sleep_impact.json) | `analyze_food_sleep_impact` | 食物/饮料对睡眠的影响分析 |

#### tools/cards/ — 卡片

| 文件 | Model Tool | 说明 |
|------|-----------|------|
| [suggest_action_card.json](tools/cards/suggest_action_card.json) | `suggest_action_card` | 行动决策卡片（多选按钮）|
| [render_health_chart.json](tools/cards/render_health_chart.json) | `render_health_chart` | 健康图表（标准/内联/一致性）|
| [suggest_sleep_adjust.json](tools/cards/suggest_sleep_adjust.json) | `suggest_sleep_adjust` | 入睡时间调整滑块卡 |
| [suggest_high_energy_window.json](tools/cards/suggest_high_energy_window.json) | `suggest_high_energy_window` | 高精力时段卡 |

#### tools/ui/ — UI 交互

| 文件 | Model Tool | 说明 |
|------|-----------|------|
| [show_status.json](tools/ui/show_status.json) | `show_status` | 进度提示（查数据前调用）|
| [suggest_replies.json](tools/ui/suggest_replies.json) | `suggest_replies` | 快捷回复按钮 |
| [set_reminder.json](tools/ui/set_reminder.json) | `set_reminder` | 定时提醒推送 |

### sub-agents/ — 子 Agent 提示词

| 文件 | 用途 | 触发时机 |
|------|------|---------|
| [README.md](sub-agents/README.md) | 子 agent 通用使用指南 | — |
| [memory-distiller.md](sub-agents/memory-distiller.md) | 从 mem0 碎片提炼用户上下文文档 | 每日 05:00 + 对话结束后异步 |
| [conversation-summarizer.md](sub-agents/conversation-summarizer.md) | 对话历史压缩为结构化摘要 | 上下文接近 token 上限 |

### assembly/ — 组装规范（面向工程团队）

| 文件 | 内容 |
|------|------|
| [context-assembly.md](assembly/context-assembly.md) | 上下文拼接逻辑、agent 循环、响应投递 |
| [tool-routing.md](assembly/tool-routing.md) | Model Tool → Server Function 映射表 |
| [token-budget.md](assembly/token-budget.md) | Token 预算分配与估算 |

## 与 Claude Code 的对标

| 维度 | Claude Code | 精力管家 |
|------|------------|---------|
| System Prompt | ~3,200 tk（66+ 文件拼接） | ~1,200 tk（4 固定片段 + 6 原子原则 + 5 行为规则 + 动态场景）|
| 工具定义 | ~11,600 tk（18+ 内置工具，含 example 块） | ~2,000 tk（13 个 Model-Facing 工具，含 example + reasoning 块）|
| 占上下文比例 | ~7.4%（of 200K） | ~1.6%（of 200K）|
| 子 Agent | 4 类（Explore/Plan/Worker/Guide） | 2 个（记忆提炼 + 对话摘要）|
| System Reminders | 40+ 种运行时注入 | 7 种系统提醒 + 4 种场景指令 |
| 行为规则 | "Doing Tasks" 原子规则 | 5 条 doing-tasks 原子规则 |
| 上下文压缩 | 有（对话摘要 + 清理） | 有（conversation-summarizer 子 agent）|
| ALL-CAPS 标记 | NEVER/ALWAYS/MUST/IMPORTANT | 全面覆盖 |
| 工具示例 | `<example>` + `<reasoning>` 块 | 关键工具含 `<example>` + `<reasoning>` 块 |

精力管家更轻量，因为：
1. C 端短对话场景（1-4 轮），不是长编程 session
2. 详细用户上下文按需拉取，不预注入
3. 工具用两层架构，Model-Facing 层精简
