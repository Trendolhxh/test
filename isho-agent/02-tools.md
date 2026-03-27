# 02 - 工具集定义

> 对应 Claude Code: `Tools Section` — 扁平列表，不分组
> 模型看到的是一个统一的工具列表；服务端/前端的路由由 orchestrator 在实现层处理

## 工具总览

| # | 工具名 | 一句话说明 | 执行侧 |
|---|--------|-----------|--------|
| 1 | get_health_data | 查询用户健康与行为数据 | 服务端 |
| 2 | get_user_profile | 了解用户是谁（作息、睡眠、生活、心理） | 服务端 |
| 3 | get_strategy | 了解该怎么做（红线、干预、认知、趋势） | 服务端 |
| 4 | save_memory | 将对话中捕获的事实写入记忆 | 服务端 |
| 5 | send_feedback_card | 向用户发送结构化反馈卡片 | 前端渲染 |
| 6 | render_analysis_card | 嵌入原生数据卡片 + AI 分析文字（复用 App 已有的 9 张健康卡片） | 前端渲染 |
| 7 | show_status | 在对话中显示进度提示（如"正在分析你的睡眠数据..."） | 前端渲染 |
| 8 | suggest_replies | 展示快捷回复按钮，减少用户打字 | 前端渲染 |
| 9 | set_reminder | 设置定时提醒推送（干预策略的执行手段） | 服务端 |

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
  "description": "了解用户是谁。加载用户的生活背景、作息习惯、睡眠状况、心理特征。用于理解用户当前消息的上下文、判断应该共情还是追问、回应用户分享的生活细节。不确定用户在说什么时先调这个。",
  "parameters": {
    "aspects": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": [
          "routines",
          "sleep_strengths",
          "sleep_issues",
          "lifestyle",
          "psychology"
        ]
      },
      "description": "要加载的方面。routines=作息模式(按典型日分类的完整时间线); sleep_strengths=睡眠做得好的(好习惯和正面表现,肯定用户时用); sleep_issues=睡眠待改善(问题+归因链:现象←原因←根因); lifestyle=生活方式(饮食/运动/环境); psychology=心理画像(压力/情绪/性格/沟通偏好)"
    }
  },
  "required": ["aspects"]
}
```

**各 aspect 的使用场景：**

| aspect | 什么时候拉 | 典型触发 |
|--------|----------|---------|
| `routines` | 需要知道用户某天的作息来理解上下文 | "今天加班好累"→查加班日模式; 加班日睡眠数据→理解为什么差 |
| `sleep_strengths` | 需要肯定用户、给正面反馈 | 用户分享好消息; 数据有改善; 反馈卡"做到了" |
| `sleep_issues` | 需要理解用户问题的根因来分析或建议 | 用户问"为什么我总是睡不够"; 解读差的数据 |
| `lifestyle` | 用户提到饮食/运动/环境相关话题 | "我最近换了窗帘"; "要不要少喝咖啡" |
| `psychology` | 用户表达情绪、或需要判断怎么说不会引起反感 | "好焦虑"; 反馈卡"没做到"需要理解心理阻力 |

**设计说明：**
- 拆为独立工具而非 `get_user_context` 加 domain 参数，原因：工具描述精准引导模型"什么时候该调哪个"，语义更清晰。
- 模型在一次对话中可多次调用，每次取不同的 aspects。已返回的 section 内容留在对话上下文中，不需要重复拉取。

---

## 工具 3：get_strategy

```json
{
  "name": "get_strategy",
  "description": "了解该怎么做。加载和用户合作的策略信息：什么不能碰、当前在推什么干预、用户的认知水平和误区。用于给建议、回应反馈卡、决定是否引导认知、规划下一步。要给行动建议或涉及干预相关话题时调这个。",
  "parameters": {
    "aspects": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": [
          "redlines",
          "active",
          "history",
          "preferences",
          "cognition",
          "trends"
        ]
      },
      "description": "要加载的方面。redlines=红线与约束(明确拒绝的方向+原话+软约束); active=当前活跃干预(方向/具体措施/状态/数据/阻力/下一步路径); history=干预历史(最近10条,每条含结果/数据/学习); preferences=干预偏好(用户接受什么类型的方法); cognition=睡眠认知(用户已有的正确认知+误区及引导方向+适合的说服方式); trends=近期趋势(周对比数据+干预日vs非干预日)"
    }
  },
  "required": ["aspects"]
}
```

**各 aspect 的使用场景：**

| aspect | 什么时候拉 | 典型触发 |
|--------|----------|---------|
| `redlines` | 要给建议前确认边界 | "有什么建议"; 需要确认某方向能不能提 |
| `active` | 涉及当前干预的任何对话 | 反馈卡回收; 新睡眠数据关联干预效果; 推送点击 |
| `history` | 需要参考过去尝试过什么 | 当前干预无效需要换方向; 用户问"之前试过什么" |
| `preferences` | 要设计新的干预方案 | 准备给新建议; 当前方案调整 |
| `cognition` | 用户说了和睡眠认知相关的话、或需要决定怎么解释 | "周末补回来就行了"; "几点睡有什么区别"; 数据解读时考虑怎么表达 |
| `trends` | 需要用数据说话 | 聊最近变化; 新睡眠数据推送; 给用户看进步 |

**场景 → 工具调用映射：**

| 场景 | 调用 | 理由 |
|------|------|------|
| "今天加班好累" | 不调 或 `get_user_profile(["routines"])` | 速览已够; 想关联加班模式时查 routines |
| "我最近睡得怎么样" | `get_strategy(["trends"])` | 需要数据趋势做解读 |
| "有什么建议" | `get_strategy(["redlines", "active", "cognition"])` | 避红线+沿当前方向+顺认知引导 |
| 反馈卡: 做到了 | `get_strategy(["active"])` + `get_user_profile(["sleep_strengths"])` | 干预详情+肯定用户 |
| 反馈卡: 没做到 | `get_strategy(["active"])` + `get_user_profile(["psychology"])` | 干预详情+理解心理阻力 |
| 新睡眠数据推送 | `get_strategy(["trends", "active"])` | 数据趋势+关联干预效果 |
| 用户提到咖啡 | `get_strategy(["redlines", "cognition"])` | 确认红线+看认知状态 |
| 用户表达焦虑 | `get_user_profile(["psychology"])` | 理解压力模式，决定共情方式 |
| 纯闲聊 | 不调 | 速览足够 |

---

## 工具 4：save_memory

```json
{
  "name": "save_memory",
  "description": "将对话中捕获的用户事实写入记忆。当用户透露生活细节、表达偏好/拒绝、反馈干预效果时调用。写入的内容会在下次运行时提炼进用户上下文文档。",
  "parameters": {
    "content": {
      "type": "string",
      "description": "要记录的事实，用自然语言描述。如：'用户说周三固定加班到 21 点'、'闹钟提醒放手机的干预，用户反馈没有执行，原因是加班太晚'"
    },
    "category": {
      "type": "string",
      "enum": ["routine_detail", "sleep_positive", "sleep_negative", "intervention_feedback", "preference", "cognition", "environment"],
      "description": "记忆类别。routine_detail=作息/生活细节，sleep_positive=睡眠正向信息，sleep_negative=睡眠负向信息，intervention_feedback=干预执行反馈，preference=偏好或拒绝，cognition=认知表达/误区，environment=环境/设备变化"
    }
  },
  "required": ["content", "category"]
}
```

**设计说明：**
- 主 agent 只管"记下来"，不管怎么组织——组织工作交给子 agent。
- content 用自然语言，不用结构化格式。
- category 从 5 类细化为 7 类，与 V3 的 section 粒度对齐：
  - `life_detail` → 拆为 `routine_detail`（作息）+ `environment`（环境变化）
  - `sleep_feedback` → 拆为 `sleep_positive`（正面）+ `sleep_negative`（负面）
  - 新增 `cognition`（用户的认知表达/误区），方便子 agent 更新 `# [cognition]` section

**调用示例：**
```
save_memory(
  content="用户说最近换了遮光窗帘，感觉早上不容易被光线吵醒了",
  category="environment"
)

save_memory(
  content="闹钟提醒放手机的干预：用户反馈昨晚执行了，感觉确实比平时早睡了半小时",
  category="intervention_feedback"
)

save_memory(
  content="用户明确表示不想讨论饮酒话题",
  category="preference"
)

save_memory(
  content="用户说'周末补回来就行了'——这是一个需要引导的认知误区",
  category="cognition"
)
```

---

## 工具 5：send_feedback_card

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

用户提交反馈后，数据自动写入记忆（category: intervention_feedback）。子 agent 下次运行时会将反馈提炼进 `# [active]` 和 `# [history]` sections。主 agent 不需要额外处理——回流由服务端 + 子 agent 自动完成。

---

## 工具 6：render_analysis_card

```json
{
  "name": "render_analysis_card",
  "description": "在对话中嵌入原生数据卡片，并附带 AI 的文字分析。你只负责选择卡片类型、视图维度，以及提供分析文字。当用户询问数据趋势、或你需要呈现数据结论时调用。",
  "parameters": {
    "cards": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "metric_key": {
            "type": "string",
            "enum": [
              "heart_rate",
              "stress",
              "activity",
              "sleep_detail",
              "sleep_efficiency",
              "blood_oxygen",
              "hrv",
              "resting_heart_rate",
              "sleep_consistency"
            ],
            "description": "原生卡片类型，对应 NativeCardRegistry 中的 metricKey"
          },
          "view_mode": {
            "type": "string",
            "enum": ["daily", "weekly", "monthly"],
            "description": "默认展示的视图维度。不传时由前端根据上下文自动选择"
          }
        },
        "required": ["metric_key"]
      },
      "description": "要展示的原生卡片列表，通常 1 张，关联对比场景最多 3 张"
    },
    "summary": {
      "type": "string",
      "description": "AI 的分析结论，1-3 句话，展示在卡片区域的上方或下方"
    },
    "highlights": {
      "type": "array",
      "items": { "type": "string" },
      "description": "关键洞察标签，如 ['深睡连续 3 天达标', '入睡比上周早了 40 分钟']"
    }
  },
  "required": ["cards", "summary"]
}
```

**设计说明：**
- **复用原生卡片，不生成图表数据。** App 已有 9 张精美的原生健康卡片（HeartRateCard、SleepDetailCard 等），全部从 Apple Health 本地取数据自渲染。agent 不需要也不应该生成 chart_type、x/y 坐标、series 等图表数据——这既浪费 token，又可能因幻觉导致数据错误。
- metric_key 的 enum 与 `NativeCardRegistry` 一一对应，前端收到后直接查表渲染，零歧义。
- view_mode 可选。大部分场景前端自动选择即可，只在用户明确说"看最近一周"时传 `weekly`。
- cards 是数组，支持关联对比场景（如同时展示 sleep_detail + hrv）。
- **agent 的真正价值在 summary 和 highlights**——用自然语言解读数据、跨指标关联分析，这是原生卡片做不到的。

**分析卡片 UI 示意：**
```
用户看到:
  ┌─────────────────────────────────────┐
  │  ┌──────────────┐ ┌──────────────┐  │
  │  │深睡连续3天达标│ │入睡早了40分钟 │  │  ← highlights 标签
  │  └──────────────┘ └──────────────┘  │
  │                                     │
  │  ┌─────────────────────────────────┐│
  │  │                                 ││
  │  │     [ 原生 SleepDetailCard ]     ││  ← 复用 App 已有卡片
  │  │     （自带日/周/月切换）          ││
  │  │                                 ││
  │  └─────────────────────────────────┘│
  │                                     │
  │  这周深睡占比从 16% 涨到 19%，手机   │  ← summary
  │  放客厅那两天效果最明显。            │
  │                                     │
  │                    精力管家 · 分析报告 │
  └─────────────────────────────────────┘
```

---

## 工具 7：show_status

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

## 工具 8：suggest_replies

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

## 工具 9：set_reminder

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
