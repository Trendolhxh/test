# Model-Facing → Server-Side 工具路由

> 面向工程团队：模型看到的工具如何映射到服务端实际接口

## 两层架构

```
Model-Facing Tools（模型看到的 13 个工具）
        ↓ orchestrator 路由
Server-Side Functions（服务端 RPC 接口）
```

模型只需做意图决策（"查什么数据"），orchestrator 负责翻译为具体的服务端调用。

## 路由映射表

### 健康数据：get_health_data → 多个 RPC

模型传入 `metrics` 数组，orchestrator 按指标拆分为对应的服务端函数，并行调用后合并结果返回。

| Model metrics 枚举值 | Server Function | 备注 |
|---|---|---|
| `sleep_stages` | `get_sleep_data(days=N)` | 包含深睡/REM/浅睡/清醒/入睡潜伏期 |
| `sleep_debt` | `get_daily_health_metrics(days=N)` | 从综合指标中提取 |
| `sleep_consistency` | `get_daily_health_metrics(days=N)` | 从综合指标中提取；不是睡眠效率 |
| `heart_rate` | `get_heart_rate(days=N)` | 日级静息心率 |
| `resting_heart_rate` | `get_heart_rate(days=N)` | 同 heart_rate |
| `hrv_sdnn` | `get_hrv_data(days=N)` | 按夜聚合 HRV 毫秒 |
| `blood_oxygen` | `get_blood_oxygen(days=N)` | 按夜聚合 SpO₂ |
| `active_energy` | `get_activity(days=N)` | 每日活动消耗千卡 |
| `steps` | `get_activity(days=N)` | 每日步数 |
| `workouts` | `get_workouts(days=N)` | 锻炼记录 |
| `respiratory_rate` | `get_daily_health_metrics(days=N)` | 从综合指标中提取 |
| `screen_time` | 端上直接获取 | 非服务端 RPC |
| `high_energy_hours_total` | iSho 算法服务 | 专有算法 |
| `high_energy_hours_remaining` | iSho 算法服务 | 专有算法 |

`date_range` 转换规则：
- `today` → `days=1`
- `7d` → `days=7`
- `14d` → `days=14`
- `30d` → `days=30`

多个 metrics 映射到同一个 RPC 时（如 `steps` + `active_energy` 都走 `get_activity`），orchestrator 只调用一次并提取对应字段。

### 记忆类：直通

| Model Tool | Server Function | 备注 |
|---|---|---|
| `get_user_profile(aspects=[...])` | 按 aspect 从用户上下文文档提取对应 section | 内部查表提取，非外部 RPC |
| `get_strategy(aspects=[...])` | 按 aspect 从用户上下文文档提取对应 section | 内部查表提取，非外部 RPC |
| `save_memory(content, category)` | `mem0.add(user_id, ...)` | 写入 mem0 事实层 |

Section 提取映射：
```
get_user_profile.routines        → 文档 # [routines]
get_user_profile.sleep_strengths → 文档 # [sleep_strengths]
get_user_profile.sleep_issues    → 文档 # [sleep_issues]
get_user_profile.lifestyle       → 文档 # [lifestyle]
get_user_profile.psychology      → 文档 # [psychology]

get_strategy.redlines            → 文档 # [redlines]
get_strategy.active              → 文档 # [active]
get_strategy.history             → 文档 # [history]
get_strategy.preferences         → 文档 # [preferences]
get_strategy.cognition           → 文档 # [cognition]
get_strategy.trends              → 文档 # [trends]
```

### 事件类：直通

| Model Tool | Server Function | 备注 |
|---|---|---|
| `record_event(...)` | `record_event(...)` | 直接透传，服务端做槽位校验 |
| `analyze_food_sleep_impact(...)` | `analyze_food_sleep_impact(...)` | 服务端内部调小模型分析 |

### 卡片类：映射

| Model Tool | Server Function / Client Protocol | 备注 |
|---|---|---|
| `suggest_action_card(...)` | `structured.cards[{cardType: "actionCard"}]` | 前端按 cardType 渲染 |
| `render_health_chart(chart_type="standard")` | `structured.cards[{cardType: "healthChartCard", metricKey}]` | 客户端二次拉数据渲染 |
| `render_health_chart(chart_type="inline")` | `structured.cards[{cardType: "inlineChartCard", dataPoints}]` | 数据直出 |
| `render_health_chart(chart_type="sleep_consistency")` | `structured.cards[{cardType: "sleepConsistencyChartCard"}]` | 专用卡类型 |
| `suggest_sleep_adjust(...)` | `structured.cards[{cardType: "sleepTimeAdjustCard"}]` | 滑块交互卡 |
| `suggest_high_energy_window(...)` | `structured.cards[{cardType: "highEnergyWindowCard"}]` | 时间区间卡 |

### UI 类：前端协议

| Model Tool | 处理方式 | 返回给模型 |
|---|---|---|
| `show_status(message)` | 即时投递给前端，不等循环结束 | `{"success": true}` |
| `suggest_replies(replies)` | 暂存，随最终响应一起投递 | `{"success": true}` |
| `set_reminder(time, message, repeat)` | 注册到推送服务 | `{"success": true}` |

前端工具统一返回 `{"success": true}`，模型不需要看到渲染结果。

## 工具白名单

实际对话中加载哪些工具由对话技能（skill）的 `toolAllowlist` 控制。不是每次都带全部 13 个工具。

| 技能场景 | 加载的 Model-Facing 工具 |
|----------|--------------------------|
| 标准对话（默认） | 全部 13 个 |
| 安全模式 / 危机支持 | 无健康工具，仅 suggest_replies |
| 数据查看专用 | get_health_data, render_health_chart, show_status, suggest_replies |
| 新用户引导 | save_memory, suggest_replies, show_status |
