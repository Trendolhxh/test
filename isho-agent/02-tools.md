# 02 - 工具集定义

> 对应 Claude Code: `Tools Section` — 扁平列表，不分组
> 模型看到的是一个统一的工具列表；服务端/前端的路由由 orchestrator 在实现层处理

## 工具总览

| # | 工具名 | 一句话说明 | 执行侧 |
|---|--------|-----------|--------|
| 1 | get_health_data | 查询用户健康与行为数据 | 服务端 |
| 2 | get_user_context | 加载用户画像和干预策略（两份 md） | 服务端（orchestrator 自动执行，不在工具列表中） |
| 3 | save_memory | 将对话中捕获的事实写入 mem0 | 服务端 |
| 4 | send_feedback_card | 向用户发送结构化反馈卡片 | 前端渲染 |
| 5 | render_analysis_card | 渲染数据分析图表卡片（可截图分享） | 前端渲染 |
| 6 | show_status | 在对话中显示进度提示（如"正在分析你的睡眠数据..."） | 前端渲染 |
| 7 | suggest_replies | 展示快捷回复按钮，减少用户打字 | 前端渲染 |
| 8 | set_reminder | 设置定时提醒推送（干预策略的执行手段） | 服务端 |

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

## 工具 2：get_user_context

```json
{
  "name": "get_user_context",
  "description": "加载用户的画像和干预策略。返回两份文档：用户画像（背景、作息模式、睡眠与精力全貌）和干预策略（红线、当前干预、历史）。每次对话开始时必须调用一次。",
  "parameters": {}
}
```

**设计说明：**
- 无参数，一次性返回两份 md。合计 ~800 token，无需分段。
- 两份 md 由子 agent 维护（从 mem0 + 健康数据提炼），主 agent 只读不写。
- 文档结构详见 [03-memory.md](./03-memory.md)。

**返回示例：**
```json
{
  "user_profile": "# 用户画像\n# 更新于 2026-03-24 05:00\n\n基本信息:\n  男, 30岁, 夜猫子型, 互联网产品经理\n\n作息模式:\n  常规工作日(一二四):\n    工作10:00-19:00, 晚餐~20:30, 刷手机→~01:30入睡, 08:45起床\n  加班日(周三固定):\n    工作到~21:00, 外卖, 刷手机→~02:00入睡, 需要\"补偿性娱乐\"\n  周五:\n    常有聚餐, 社交→~02:30入睡, 次日自然醒\n  周末:\n    ~02:30入睡, ~10:30起床\n  备注:\n    - 下午一杯咖啡是刚需\n    - 周日晚会焦虑周一\n\n睡眠与精力状况:\n  做得好的:\n    - 工作日起床时间稳定(08:45), 无赖床\n    - 入睡潜伏期正常(~15min), 上床后较快入睡\n    - 夜间觉醒少, 睡眠连续性好\n    - 最近开始尝试行为干预, 执行日效果明显\n  待改善:\n    - 睡眠时长不足(工作日均6.5h) ← 上床过晚 ← 睡前刷手机1.5-2h\n    - 深睡占比偏低(18%) ← 可能与睡前屏幕刺激有关(待确认)\n    - 周末作息后移 ← 补觉+社交晚归, 周一生物钟紊乱\n\n近期变化:\n  - 深睡 16%→18%(W12 vs W11), 略有改善\n  - \"手机放客厅\"干预执行2天, 入睡提前45min",
  "intervention_plan": "# 干预策略\n# 更新于 2026-03-24 05:00\n\n红线:\n  - 限制咖啡: \"下午必须靠咖啡撑着\"\n  - 早起运动: \"早上根本起不来\"\n\n当前干预:\n  方向: 减少睡前手机使用, 建立wind-down环节\n  活跃:\n    - 每晚11点闹钟提醒放手机到客厅(3.23开始, 待反馈)\n  下一步:\n    - 有效 → 固化习惯, 逐步提前到10:30\n    - 无效 → 尝试手机定时锁屏类工具辅助\n\n干预历史:\n  - 手机放客厅(3.20-3.22): 部分有效, 执行日入睡提前45min/深睡+3%, 加班日做不到\n  - 限制下午咖啡(3.18): 用户拒绝 → 红线\n  - 早起运动(3.15): 用户拒绝 → 红线",
  "updated_at": "2026-03-24T05:00:00+08:00"
}
```

---

## 工具 3：save_memory

```json
{
  "name": "save_memory",
  "description": "将对话中捕获的用户事实写入 mem0。当用户透露生活细节、表达偏好/拒绝、反馈干预效果时调用。写入的内容会被子 agent 在下次运行时提炼进用户画像和干预策略。",
  "parameters": {
    "content": {
      "type": "string",
      "description": "要记录的事实，用自然语言描述。如：'用户说周三固定加班到 21 点'、'闹钟提醒放手机的干预，用户反馈没有执行，原因是加班太晚'"
    },
    "category": {
      "type": "string",
      "enum": ["life_detail", "sleep_feedback", "intervention_feedback", "preference", "other"],
      "description": "记忆类别。life_detail=生活细节，sleep_feedback=睡眠相关感受，intervention_feedback=干预反馈，preference=偏好或拒绝"
    }
  },
  "required": ["content", "category"]
}
```

**设计说明：**
- 主 agent 只管"记下来"，不管怎么组织——组织工作交给子 agent。
- content 用自然语言，不用结构化格式。mem0 擅长处理非结构化文本。
- category 帮助子 agent 更快地对记忆分类和提炼。

**调用示例：**
```
save_memory(
  content="用户说最近换了遮光窗帘，感觉早上不容易被光线吵醒了",
  category="life_detail"
)

save_memory(
  content="闹钟提醒放手机的干预：用户反馈昨晚执行了，感觉确实比平时早睡了半小时",
  category="intervention_feedback"
)

save_memory(
  content="用户明确表示不想讨论饮酒话题",
  category="preference"
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

用户提交反馈后，数据自动写入 mem0（category: intervention_feedback）。子 agent 下次运行时会将反馈提炼进干预策略.md 的干预历史中。主 agent 不需要额外处理——回流由服务端 + 子 agent 自动完成。

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

---

## 工具 6：show_status

```json
{
  "name": "show_status",
  "description": "在对话中显示一条进度提示。当即将执行耗时操作（如查询数据、生成分析）时调用，让用户知道 agent 正在工作。提示会在后续回复到达后自动消失。",
  "parameters": {
    "message": {
      "type": "string",
      "description": "进度提示文案，如'正在分析你过去一周的睡眠数据...'"
    }
  },
  "required": ["message"]
}
```

**设计说明：**
- 对标 Claude Code 的 TodoWrite 进度可见性——用户知道 agent 在做什么，不是卡住了。
- 1 个参数，极轻量。前端收到后渲染为加载态提示，后续消息到达后自动替换。
- 典型用法：先调 show_status，再调 get_health_data，用户看到的是"正在分析..."而非空白等待。

---

## 工具 7：suggest_replies

```json
{
  "name": "suggest_replies",
  "description": "在回复下方展示快捷回复按钮。用户点击按钮等同于发送对应文本。用于降低用户回复门槛，引导对话方向。",
  "parameters": {
    "replies": {
      "type": "array",
      "items": { "type": "string" },
      "description": "快捷回复选项，最多 4 个，每个不超过 15 字"
    }
  },
  "required": ["replies"]
}
```

**设计说明：**
- 移动端打字成本高，快捷按钮大幅降低回复门槛。
- 限制 4 个、15 字以内，避免选项过多造成决策负担。
- 用户点击等同于发送文本消息，不引入额外交互协议。
- 典型场景：
  - agent 问"你昨晚睡得怎么样？" → `["还不错", "一般般", "很差", "不想聊这个"]`
  - agent 给完分析 → `["给我个建议", "看详细数据", "知道了"]`

---

## 工具 8：set_reminder

```json
{
  "name": "set_reminder",
  "description": "设置一条定时提醒推送。用于配合干预策略，在关键时间点提醒用户执行行动。如'22:30 提醒放下手机'。",
  "parameters": {
    "time": {
      "type": "string",
      "description": "提醒时间，ISO 8601 格式（如 '2026-03-24T22:30:00+08:00'）或相对时间（如 'today 22:30'）"
    },
    "message": {
      "type": "string",
      "description": "提醒内容，简短直接，如'该放下手机了，把它放到客厅充电吧'"
    },
    "repeat": {
      "type": "string",
      "enum": ["once", "daily", "weekdays", "weekends"],
      "description": "重复规则。once=仅一次，daily=每天，weekdays=工作日，weekends=周末"
    }
  },
  "required": ["time", "message"]
}
```

**设计说明：**
- 干预策略的**执行闭环**：agent 给出建议 → 设置提醒帮用户执行 → 反馈卡片收集结果。没有提醒，很多建议就停在"知道了但做不到"。
- repeat 支持按工作日/周末重复，匹配用户画像中的作息模式分类。
- repeat 默认不传时为 once，避免 agent 随意设置重复提醒打扰用户。
- message 应该是行动导向的（"把手机放到客厅"），不是说教式的（"你该睡了"）。

**提醒 UI 示意（推送通知）：**
```
┌─────────────────────────────┐
│ 🌙 精力管家                  │
│ 该放下手机了，               │
│ 把它放到客厅充电吧           │
│                    22:30    │
└─────────────────────────────┘
```
