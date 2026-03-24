# 02 - 工具集定义

> 对应 Claude Code: `Tools Section` — 扁平列表，不分组
> 模型看到的是一个统一的工具列表；服务端/前端的路由由 orchestrator 在实现层处理

## 工具总览

| # | 工具名 | 一句话说明 | 执行侧 |
|---|--------|-----------|--------|
| 1 | get_health_data | 查询用户健康与行为数据 | 服务端 |
| 2 | get_user_profile | 读取用户画像（偏好、历史反馈、基础信息） | 服务端 |
| 3 | update_user_profile | 新增或更新用户画像中的某个字段 | 服务端 |
| 4 | send_feedback_card | 向用户发送结构化反馈卡片 | 前端渲染 |
| 5 | render_analysis_card | 渲染数据分析图表卡片（可截图分享） | 前端渲染 |

> 注："执行侧"列不会出现在实际 prompt 中，仅供工程团队做路由参考。

---

## 工具 1：get_health_data

```json
{
  "name": "get_health_data",
  "description": "查询用户的健康与行为数据。支持查询今日实时值或过去 N 天的历史趋势。一次调用可查询多个指标。",
  "parameters": {
    "metrics": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": [
          "high_energy_hours_total",
          "high_energy_hours_remaining",
          "sleep_stages",
          "sleep_debt",
          "sleep_consistency",
          "heart_rate",
          "resting_heart_rate",
          "hrv_sdnn",
          "active_energy",
          "steps",
          "workouts",
          "blood_oxygen",
          "respiratory_rate",
          "screen_time"
        ]
      },
      "description": "要查询的指标列表"
    },
    "date_range": {
      "type": "string",
      "enum": ["today", "7d", "14d", "30d"],
      "description": "查询时间范围。today 返回实时值，其余返回每日汇总数组"
    }
  },
  "required": ["metrics", "date_range"]
}
```

**设计说明：**
- 用一个工具 + metrics 数组，而非 14 个独立工具。对标 Claude Code 的 Bash（一个工具覆盖大量操作），减少工具数量降低模型选择负担。
- date_range 用枚举而非自由日期，防止模型生成奇怪的日期格式。
- sleep_stages 返回结果中包含入睡时间、起床时间、各分期时长。

**返回结构示例（由服务端定义）：**
```json
{
  "query_date_range": "7d",
  "results": {
    "sleep_stages": [
      {
        "date": "2026-03-23",
        "bedtime": "01:15",
        "wake_time": "08:30",
        "total_minutes": 435,
        "deep_minutes": 85,
        "rem_minutes": 110,
        "light_minutes": 210,
        "awake_minutes": 30
      }
    ],
    "resting_heart_rate": [
      { "date": "2026-03-23", "value": 62, "unit": "bpm" }
    ]
  }
}
```

---

## 工具 2：get_user_profile

```json
{
  "name": "get_user_profile",
  "description": "读取用户画像。返回完整的用户睡眠笔记，包括背景、睡眠现状、干预记录和禁忌方向。每次对话开始时应调用一次。",
  "parameters": {}
}
```

**设计说明：**
- 无参数，返回完整文档。文档本身足够短（~300 token），不需要分段加载。
- 字段结构详见 [03-memory.md](./03-memory.md)。

**返回示例：**
```json
{
  "background": {
    "age": 30,
    "chronotype": "night_owl",
    "work": "互联网，常加班到 21-22 点",
    "evening_routine": "下班后刷手机到入睡，基本没有 wind-down",
    "notes": "下午必须喝咖啡（不要建议限制）"
  },
  "sleep_status": {
    "avg_bedtime": "01:30",
    "avg_deep_sleep_pct": 18,
    "main_issues": ["入睡困难：睡前手机使用", "周末作息后移导致周一状态差"],
    "trend": "略有改善（深睡 16% → 18%）",
    "updated": "2026-03-23"
  },
  "interventions": [
    { "method": "晚 10 点手机放客厅", "result": "有效但难坚持，加班日做不到", "period": "3.20-3.22" },
    { "method": "限制下午咖啡", "result": "用户拒绝" },
    { "method": "每晚 11 点闹钟提醒放手机", "result": "进行中", "started": "3.23" }
  ],
  "do_not_suggest": ["限制咖啡", "早起运动"]
}
```

---

## 工具 3：update_user_profile

```json
{
  "name": "update_user_profile",
  "description": "更新用户画像中的信息。当用户透露新的生活细节、完成干预反馈、或需要记录新的禁忌方向时调用。",
  "parameters": {
    "field": {
      "type": "string",
      "description": "要更新的字段路径，如 'background.work'、'interventions'、'do_not_suggest'"
    },
    "action": {
      "type": "string",
      "enum": ["set", "append"],
      "description": "set=覆盖值，append=追加到数组"
    },
    "value": {
      "type": "any",
      "description": "要写入的值"
    }
  },
  "required": ["field", "action", "value"]
}
```

**调用示例：**
```
# 记录新的干预
update_user_profile(
  field="interventions",
  action="append",
  value={ method: "每晚 11 点闹钟提醒放手机", result: "进行中", started: "3.23" }
)

# 记录禁忌方向
update_user_profile(
  field="do_not_suggest",
  action="append",
  value="限制咖啡"
)

# 更新工作信息
update_user_profile(
  field="background.work",
  action="set",
  value="互联网，最近转了新组，加班减少"
)
```

---

## 工具 4：send_feedback_card

```json
{
  "name": "send_feedback_card",
  "description": "向用户发送一张结构化反馈卡片，用于收集用户对某条行动建议的执行反馈。卡片会在建议的预计执行时间之后、用户下次打开 App 时展示。用户看到卡片时会明确知道'这是在向精力管家反馈'，他的回答会影响后续建议。仅在给出行动建议时调用。",
  "parameters": {
    "suggestion_id": {
      "type": "string",
      "description": "关联的建议 ID（由服务端生成）"
    },
    "check_question": {
      "type": "string",
      "description": "向用户确认的问题，如'昨晚你有没有在 10 点后把手机放到客厅？'"
    },
    "completion_options": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "label": { "type": "string" },
          "value": { "type": "string" }
        }
      },
      "description": "确定性选项按钮，用户必选其一"
    },
    "follow_up_prompt": {
      "type": "string",
      "description": "开放式追问提示语，如'有什么想补充的吗？（选填）'"
    },
    "scheduled_after": {
      "type": "string",
      "description": "反馈卡片最早展示时间，ISO 8601 格式。如建议是'今晚 11 点前上床'，则设为明天早上。"
    }
  },
  "required": ["suggestion_id", "check_question", "completion_options", "follow_up_prompt", "scheduled_after"]
}
```

**设计说明：**
- **确定性意图 + 开放式补充**的双层结构：completion_options 是必选按钮（结构化），follow_up_prompt 是选填文字框（开放式）。
- completion_options 由模型根据建议内容动态生成，而非固定死选项。比如：
  - 行为类建议 → `["做到了", "部分做到", "没做到"]`
  - 设置类建议 → `["已开启", "没开启"]`
- check_question 让用户明确知道"这是在问我上次那个建议做得怎样"。
- scheduled_after 控制展示时机，避免建议刚给出就弹反馈。
- 卡片本身的视觉设计应传达"这是给精力管家的反馈"的预期（品牌色、icon、文案）。

**反馈卡片 UI 示意：**
```
┌─────────────────────────────────────┐
│  🔄 精力管家想知道                    │
│                                     │
│  昨晚你有没有在 10 点后               │
│  把手机放到客厅？                     │
│                                     │
│  ┌──────┐ ┌────────┐ ┌──────┐      │
│  │做到了 │ │部分做到 │ │没做到│       │
│  └──────┘ └────────┘ └──────┘      │
│                                     │
│  有什么想补充的吗？（选填）            │
│  ┌─────────────────────────────┐    │
│  │                             │    │
│  └─────────────────────────────┘    │
│                         [提交反馈]   │
└─────────────────────────────────────┘
```

**反馈数据回流：**

用户提交反馈后，数据自动写入 suggestion_history，下次调用 get_user_profile 时 agent 可以看到。agent 不需要额外调用工具处理反馈——反馈的回流是服务端自动完成的。

---

## 工具 5：render_analysis_card

```json
{
  "name": "render_analysis_card",
  "description": "渲染一张数据分析图表卡片，附带文字摘要。卡片为截图友好设计，便于用户分享。当用户询问自己的数据趋势、或 agent 需要用可视化方式呈现分析结论时调用。",
  "parameters": {
    "title": {
      "type": "string",
      "description": "卡片标题，如'过去 7 天睡眠趋势'"
    },
    "chart": {
      "type": "object",
      "properties": {
        "chart_type": {
          "type": "string",
          "enum": ["line", "bar", "stacked_bar", "ring"],
          "description": "图表类型"
        },
        "x_label": { "type": "string" },
        "y_label": { "type": "string" },
        "series": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "name": { "type": "string" },
              "data": {
                "type": "array",
                "items": {
                  "type": "object",
                  "properties": {
                    "x": { "type": "string" },
                    "y": { "type": "number" }
                  }
                }
              }
            }
          }
        }
      },
      "description": "图表定义"
    },
    "summary": {
      "type": "string",
      "description": "1-3 句话的文字摘要，写在图表下方"
    },
    "highlights": {
      "type": "array",
      "items": { "type": "string" },
      "description": "关键洞察要点，以标签形式展示在卡片上，如 ['深睡占比提升 12%', 'HRV 连续 3 天上升']"
    }
  },
  "required": ["title", "chart", "summary"]
}
```

**设计说明：**
- chart_type 限定 4 种，覆盖睡眠分期（stacked_bar）、趋势（line）、对比（bar）、占比（ring）。
- series 结构让模型可以叠加多条数据线（如同时展示深睡和 HRV 的相关性）。
- highlights 是可选的标签式洞察，便于用户截图后一目了然。
- summary 是模型生成的自然语言总结，写在图表下方。

**分析卡片 UI 示意：**
```
┌─────────────────────────────────────┐
│  过去 7 天睡眠趋势                    │
│                                     │
│  ████                               │
│  ████ ██                            │
│  ████ ████ ██                       │
│  ████ ████ ████ ████ ...            │
│  Mon  Tue  Wed  Thu  ...            │
│                                     │
│  ┌──────────────┐ ┌──────────────┐  │
│  │深睡占比提升12%│ │HRV连续3天上升│   │
│  └──────────────┘ └──────────────┘  │
│                                     │
│  这周你的深度睡眠占比从 18% 提升到    │
│  22%，可能与减少睡前刷手机有关。      │
│  HRV 也在同步改善，说明身体恢复       │
│  能力在增强。                        │
│                                     │
│                    精力管家 · 分析报告 │
└─────────────────────────────────────┘
```
