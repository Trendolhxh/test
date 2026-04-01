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
┌─ tool-descriptions（~1,200 tk）───────────────┐
│  8 个 Model-Facing 工具描述 + 2 个通用规则       │
│  复杂工具拆独立使用域，按场景选择性注入           │
│  orchestrator 路由到 Server-Side RPC           │
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

### tool-descriptions/ — 工具描述（对标 Claude Code 的 tool description + system-prompt-tool-usage 系列）

每个 `.md` 文件只写 description（写给模型看的使用手册），不写调用接口（参数 schema 等由研发定义）。扁平目录结构，文件名即用途说明。

复杂工具（get_health_data、get_strategy）的不同使用域拆成独立文件，orchestrator 按场景选择性注入。

#### 通用工具规则

注入 system prompt，对所有工具生效。

| 文件 | 内容 |
|------|------|
| [common-call-discipline.md](tool-descriptions/tool-description-common-call-discipline.md) | 不是每条消息都需要工具；不确定时不调；连续2次失败后停止；已返回数据不重复请求 |
| [common-visibility-rules.md](tool-descriptions/tool-description-common-visibility-rules.md) | 哪些工具结果对用户可见/静默，文本如何配合每类工具输出 |

#### get_health_data — 健康数据查询（拆 3 个独立使用域）

| 文件 | 注入时机 | 内容 |
|------|---------|------|
| [get-health-data.md](tool-descriptions/tool-description-get-health-data.md) | 始终 | 工具能力、14 种指标、4 种时间范围、按话题选指标映射表、渐进式查询策略、空数据降级 |
| [get-health-data-do-not-call-scenarios.md](tool-descriptions/tool-description-get-health-data-do-not-call-scenarios.md) | 标准对话 | 不该调用的场景：情绪表达先回应、科普用模型知识、已拉数据不重复 |
| [get-health-data-interpret-anomalies.md](tool-descriptions/tool-description-get-health-data-interpret-anomalies.md) | 标准对话 | 异常值处理：先查数据源/设备→关联生活事件→声明局限性 |

#### get_user_profile — 用户画像

| 文件 | 注入时机 | 内容 |
|------|---------|------|
| [get-user-profile.md](tool-descriptions/tool-description-get-user-profile.md) | 始终 | 5 个 aspect 选择策略、速览够用时不调、新用户档案稀疏时多提问多 save_memory |

#### get_strategy — 干预策略（拆 1 个独立使用域）

| 文件 | 注入时机 | 内容 |
|------|---------|------|
| [get-strategy.md](tool-descriptions/tool-description-get-strategy.md) | 始终 | 6 个 aspect 选择策略、尚无方案时不凭空建议、红线冲突时说明原因 |
| [get-strategy-mandatory-before-advice.md](tool-descriptions/tool-description-get-strategy-mandatory-before-advice.md) | 标准对话 | 硬性规则：给任何行为建议前 MUST 先调此工具加载 redlines + active |

#### save_memory — 记忆写入

| 文件 | 注入时机 | 内容 |
|------|---------|------|
| [save-memory.md](tool-descriptions/tool-description-save-memory.md) | 始终 | 该存/不该存、7 个 category、格式要求、environment 用于数据质量溯源、静默操作 |

#### render_analysis_card — 分析卡片

| 文件 | 注入时机 | 内容 |
|------|---------|------|
| [render-analysis-card.md](tool-descriptions/tool-description-render-analysis-card.md) | 始终 | 9 种卡片按话题选择、卡片展示数据/文字负责解读、summary 带参考系、关联对比最多 3 张 |

#### suggest_replies — 快捷回复

| 文件 | 注入时机 | 内容 |
|------|---------|------|
| [suggest-replies.md](tool-descriptions/tool-description-suggest-replies.md) | 始终 | 提问/引导时用、倾诉时不用、连续两轮不用、含退出选项 |

#### send_feedback_card — 反馈卡

| 文件 | 注入时机 | 内容 |
|------|---------|------|
| [send-feedback-card.md](tool-descriptions/tool-description-send-feedback-card.md) | 标准对话 | 仅在有执行时间点的建议后发送、check_question 关联具体行为、次日早晨回收、2+ 张未回收不新增 |

#### set_reminder — 定时提醒

| 文件 | 注入时机 | 内容 |
|------|---------|------|
| [set-reminder.md](tool-descriptions/tool-description-set-reminder.md) | 标准对话 | 用户确认后才设、时间合理性、行动导向文案、daily 需确认 |

#### show_status — 进度提示

| 文件 | 注入时机 | 内容 |
|------|---------|------|
| [show-status.md](tool-descriptions/tool-description-show-status.md) | 始终 | 耗时操作前调用、自然语言文案、不暴露工具名 |

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
| 工具定义 | ~11,600 tk（18+ 内置工具，含 example 块） | ~1,200 tk（8 个 Model-Facing 工具 + 2 通用规则，复杂工具拆独立使用域按场景注入）|
| 占上下文比例 | ~7.4%（of 200K） | ~1.6%（of 200K）|
| 子 Agent | 4 类（Explore/Plan/Worker/Guide） | 2 个（记忆提炼 + 对话摘要）|
| System Reminders | 40+ 种运行时注入 | 7 种系统提醒 + 4 种场景指令 |
| 行为规则 | "Doing Tasks" 原子规则 | 5 条 doing-tasks 原子规则 |
| 上下文压缩 | 有（对话摘要 + 清理） | 有（conversation-summarizer 子 agent）|
| ALL-CAPS 标记 | NEVER/ALWAYS/MUST/IMPORTANT | 全面覆盖 |
| 工具示例 | `<example>` + `<reasoning>` 块 | 待补充（细化阶段逐步添加）|

精力管家更轻量，因为：
1. C 端短对话场景（1-4 轮），不是长编程 session
2. 详细用户上下文按需拉取，不预注入
3. 工具用两层架构，Model-Facing 层精简
