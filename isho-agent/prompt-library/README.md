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
│  13 个 Model-Facing 工具描述（按场景拼接注入）    │
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

### tools/ — Model-Facing 工具描述

每个 `.md` 文件只写 description（写给模型看的使用手册），不写调用接口（参数 schema 等由研发定义）。

每个工具的 description 按场景拆分为多个 section，orchestrator 在运行时按当前场景拼接注入：
- **`## base`** — 始终随工具定义注入的核心描述
- **`## standard`** — 标准对话模式下的完整使用指南（含 example）
- **`## scene:xxx`** — 特定触发场景的补充描述
- **`## data_view`** / **`## onboarding`** / **`## crisis`** — 特殊技能模式下的替代描述

#### Description 注入场景及触发条件

| 场景 key | 触发条件 | 说明 |
|----------|---------|------|
| `base` | 始终注入 | 工具的核心功能说明，任何场景都需要 |
| `standard` | 默认对话模式（无特殊技能激活） | 完整的使用时机、规则、示例 |
| `data_view` | 用户进入"数据查看"专用技能 | 精简描述，聚焦数据展示 |
| `onboarding` | 新用户首次对话，激活"引导"技能 | 聚焦初始画像捕获 |
| `crisis` | 触发安全/危机支持模式 | 仅保留情绪支持相关指引 |
| `scene:feedback_submit` | 用户提交反馈卡（做到了/没做到） | 补充反馈卡处理的 aspect 选择指引 |
| `scene:push_click` | 用户点击推送提醒进入对话 | 补充推送上下文的处理指引 |
| `scene:new_sleep_data` | 新睡眠数据到达 + 用户今天首次打开 | 补充新数据关联分析指引 |
| `scene:agent_insight` | 子 agent 标记了待推送洞察 | 补充洞察与策略一致性校验指引 |

> 拼接规则：`base` + 技能模式描述（`standard` / `data_view` / `onboarding` / `crisis`）+ 0~N 个 `scene:xxx`。一个工具在某场景下没有对应 section 则不追加。

#### tools/health/ — 健康数据

| 文件 | Model Tool | 描述 sections |
|------|-----------|---------------|
| [get_health_data.md](tools/health/get_health_data.md) | `get_health_data` | base, standard, data_view, scene:new_sleep_data |

#### tools/memory/ — 记忆系统

| 文件 | Model Tool | 描述 sections |
|------|-----------|---------------|
| [get_user_profile.md](tools/memory/get_user_profile.md) | `get_user_profile` | base, scene:feedback_submit, scene:push_click |
| [get_strategy.md](tools/memory/get_strategy.md) | `get_strategy` | base, standard, scene:feedback_submit, scene:agent_insight, scene:new_sleep_data |
| [save_memory.md](tools/memory/save_memory.md) | `save_memory` | base, standard, onboarding |

#### tools/events/ — 事件记录

| 文件 | Model Tool | 描述 sections |
|------|-----------|---------------|
| [record_event.md](tools/events/record_event.md) | `record_event` | base, standard |

#### tools/analysis/ — 分析

| 文件 | Model Tool | 描述 sections |
|------|-----------|---------------|
| [analyze_food_sleep_impact.md](tools/analysis/analyze_food_sleep_impact.md) | `analyze_food_sleep_impact` | base, standard |

#### tools/cards/ — 卡片

| 文件 | Model Tool | 描述 sections |
|------|-----------|---------------|
| [suggest_action_card.md](tools/cards/suggest_action_card.md) | `suggest_action_card` | base, standard |
| [render_health_chart.md](tools/cards/render_health_chart.md) | `render_health_chart` | base, standard, data_view, scene:new_sleep_data |
| [suggest_sleep_adjust.md](tools/cards/suggest_sleep_adjust.md) | `suggest_sleep_adjust` | base, scene:push_click |
| [suggest_high_energy_window.md](tools/cards/suggest_high_energy_window.md) | `suggest_high_energy_window` | base |

#### tools/ui/ — UI 交互

| 文件 | Model Tool | 描述 sections |
|------|-----------|---------------|
| [show_status.md](tools/ui/show_status.md) | `show_status` | base |
| [suggest_replies.md](tools/ui/suggest_replies.md) | `suggest_replies` | base, crisis, onboarding |
| [set_reminder.md](tools/ui/set_reminder.md) | `set_reminder` | base, standard |

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
| 工具定义 | ~11,600 tk（18+ 内置工具，含 example 块） | ~2,000 tk（13 个 Model-Facing 工具，description 按场景拼接注入）|
| 占上下文比例 | ~7.4%（of 200K） | ~1.6%（of 200K）|
| 子 Agent | 4 类（Explore/Plan/Worker/Guide） | 2 个（记忆提炼 + 对话摘要）|
| System Reminders | 40+ 种运行时注入 | 7 种系统提醒 + 4 种场景指令 |
| 行为规则 | "Doing Tasks" 原子规则 | 5 条 doing-tasks 原子规则 |
| 上下文压缩 | 有（对话摘要 + 清理） | 有（conversation-summarizer 子 agent）|
| ALL-CAPS 标记 | NEVER/ALWAYS/MUST/IMPORTANT | 全面覆盖 |
| 工具示例 | `<example>` + `<reasoning>` 块 | 关键工具含 `<example>` + `<reasoning>` 块（在 standard section 中）|

精力管家更轻量，因为：
1. C 端短对话场景（1-4 轮），不是长编程 session
2. 详细用户上下文按需拉取，不预注入
3. 工具用两层架构，Model-Facing 层精简
