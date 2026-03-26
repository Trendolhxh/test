# 评测数据构建方案

## 设计思路

评测分两层，对应系统架构的两层分离：

| 层 | 评测对象 | 判定方式 | 数据格式 |
|---|---------|---------|---------|
| **状态机层** | EventContext → INVOKE/SILENT 判定 | 精确断言（deterministic） | input → expected_output |
| **Agent 层** | system prompt + messages → 文本 + 工具调用 | 模糊评判（LLM-as-judge + 规则检查） | input → expected_behaviors |

## 目录结构

```
eval/
├── README.md                      # 本文件
├── 01-state-machine/              # 状态机层评测
│   └── cases.json                 # EventContext → INVOKE/SILENT
├── 02-agent/                      # Agent 层评测
│   ├── user-profiles/             # 可复用的用户画像 fixtures
│   │   ├── typical-night-owl.md   # 典型夜猫子（示例用户）
│   │   └── new-user.md            # 新用户（空画像）
│   ├── intervention-plans/        # 可复用的干预策略 fixtures
│   │   ├── phone-intervention.md  # 手机放客厅干预期
│   │   └── empty.md               # 新用户（空策略）
│   └── cases.json                 # Agent 行为评测用例
└── 03-checklist/                  # 输出质量检查清单
    └── style-rules.json           # 自动化可检查的样式规则
```

## 评测维度全景

### 状态机层（精确断言）

覆盖 07-events 的所有判定分支：

| # | 场景 | 预期 |
|---|------|------|
| 1 | user_message | INVOKE, 无场景指令 |
| 2 | feedback_submit | INVOKE, 注入反馈数据 |
| 3 | push_click | INVOKE, 注入提醒上下文 |
| 4 | app_open + agent上次说了用户没回 | SILENT |
| 5 | app_open + 30分钟内 + 无紧急洞察 | SILENT |
| 6 | app_open + 30分钟内 + 有紧急洞察 | INVOKE（洞察覆盖冷却） |
| 7 | app_open + 有待推送洞察 | INVOKE, scene=agent_insight |
| 8 | app_open + 有未看睡眠数据 | INVOKE, scene=new_sleep_data |
| 9 | app_open + 什么都没有 | SILENT |

### Agent 层（模糊评判）

按 05-agent-loop 的 5 种调用模式 × 关键场景组合：

| 模式 | 覆盖场景 | 评测重点 |
|------|---------|---------|
| 纯对话 | 日常聊天、吐槽、闲聊 | 不强行引导到睡眠话题；共情；简短 |
| 查数据→回复 | 用户问数据、新睡眠数据推送 | 正确调用 get_health_data；数字有对比锚点 |
| 记录→回复 | 用户透露新信息 | 正确调用 save_memory；不说"我记下了" |
| 建议+反馈卡 | 给建议、反馈卡回收后推进 | set_reminder + send_feedback_card 闭环 |
| 数据+图表 | 用户要看趋势 | get_health_data + render_analysis_card |

### 关键边界场景

| 场景 | 评测重点 |
|------|---------|
| 新用户首次对话 | 画像为空时主动提问了解用户 |
| 触碰红线 | 不建议限制咖啡、不建议早起运动 |
| 用户没做到干预 | 理解原因，不追责，调整方法 |
| 加班日特殊处理 | 降低期望，不强推 |
| 用户拒绝建议 | 尊重拒绝，记入红线/偏好 |
| 工具执行报错 | 用已有信息回复，不卡住 |
