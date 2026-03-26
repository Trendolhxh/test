# 03 - 记忆系统（v2: 按需加载）

> 用户上下文从"全量注入 system prompt"改为"模型按需查询"
> 文档按 section 组织，支持选择性提取

---

## 架构变化

```
v1 (旧):
  orchestrator 全量加载 → 两份 md 塞进 system prompt (~800 tk 每次必付)
  模型看到全部信息，无论本轮是否需要

v2 (新):
  system prompt 只放速览 (~80 tk，含红线关键词)
  ↓
  模型根据用户消息 + 速览，判断需要哪些上下文
  ↓
  调用 get_user_context(sections=["routines", "active_intervention", ...])
  ↓
  只返回请求的 section，按需注入
```

**收益：**
- 用户说"今天好累" → 模型可能只需 0-1 个 section（甚至不调），省 700+ tk
- 用户问"有什么建议" → 模型拉 redlines + active_intervention + cognition，~300 tk
- 画像可以写得更详细（总量不再受 system prompt 预算限制），按需取用时 token 仍然可控
- 多轮对话中，已拉取的 section 在上下文里，不需要重复拉取

---

## 文档结构

两份 md 合并为一份，按 section 标记分块。每个 section 有固定 key，可独立提取。

### Section 清单

| key | 名称 | 内容 | 典型大小 |
|-----|------|------|---------|
| `summary` | 速览 | 一句话人物画像 + 核心问题 + 阶段 + 红线关键词 | ~80 tk |
| `routines` | 作息模式 | 按模式归纳的作息时间线 | ~150 tk |
| `sleep` | 睡眠全貌 | 做得好的 + 待改善（含归因链）| ~180 tk |
| `lifestyle` | 生活方式 | 饮食/运动/环境/物质 | ~100 tk |
| `psychology` | 心理画像 | 压力源/应对方式/性格沟通偏好/对App态度 | ~120 tk |
| `cognition` | 睡眠认知 | 已有正确认知 + 误区 + 引导策略 | ~150 tk |
| `trends` | 近期趋势 | 最近 1-2 周的关键指标变化 | ~80 tk |
| `redlines` | 红线 | 用户明确拒绝的方向 + 原话 + 软约束 | ~100 tk |
| `active_intervention` | 当前干预 | 活跃干预 + 状态 + 已知阻力 + 下一步路径 | ~150 tk |
| `intervention_history` | 干预历史 | 最近 10 条干预记录 + 每条的结果/数据/学习 | ~150 tk |
| `intervention_preferences` | 干预偏好 | 用户对干预方式的态度特征 | ~60 tk |

> **section 设计原则：每个 section 可脱离其他 section 独立理解。** section 内部不引用其他 section 的具体内容，只在需要时用关键词指向（如"见 redlines"）。

### 文档模板

```yaml
# 用户上下文
# 更新于 {timestamp}
# 使用天数: {days} | 对话轮次: {conversations}

# [summary]
{一行人物速览} | 核心问题: {一句话} | 阶段: {阶段} | 红线: {关键词列表}

# [routines]
...

# [sleep]
...

# [lifestyle]
...

# [psychology]
...

# [cognition]
...

# [trends]
...

# [redlines]
...

# [active_intervention]
...

# [intervention_history]
...

# [intervention_preferences]
...
```

---

## System Prompt 中的速览

`summary` section 始终注入 system prompt，提供最小必要上下文：

```
## 用户速览
30岁男/产品经理/晚型人/独居 | 核心问题:睡前手机→上床晚→时长不足 | 阶段:干预中期 | 红线:咖啡,早起运动
```

**为什么速览必须包含红线关键词：** 红线是安全约束，即使模型不调用 get_user_context 也不能违反。速览中的红线关键词确保模型在任何情况下都能避开。

---

## get_user_context 工具定义

```json
{
  "name": "get_user_context",
  "description": "按需加载用户上下文信息。根据当前对话需要，选择要加载的信息模块。速览(summary)已在系统提示中，无需重复加载。不确定需要哪些时，先加载与当前话题最相关的 1-2 个 section。",
  "parameters": {
    "sections": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": [
          "routines",
          "sleep",
          "lifestyle",
          "psychology",
          "cognition",
          "trends",
          "redlines",
          "active_intervention",
          "intervention_history",
          "intervention_preferences"
        ]
      },
      "description": "要加载的上下文模块列表"
    }
  },
  "required": ["sections"]
}
```

---

## 典型查询场景

| 用户场景 | 模型应查询的 sections | 理由 |
|---------|---------------------|------|
| "今天加班好累" | 不调用 或 `routines` | 纯聊天，速览已够；如需关联加班模式可查 |
| "我最近睡得怎么样" | `trends` + `sleep` | 需要近期数据趋势 + 睡眠全貌做解读 |
| "有什么建议吗" | `redlines` + `active_intervention` + `cognition` | 避开红线 + 沿当前方向 + 顺着认知引导 |
| 反馈卡提交(做到了) | `active_intervention` | 需要知道当前干预详情来推进 |
| 反馈卡提交(没做到) | `active_intervention` + `psychology` | 需要理解阻力 + 心理背景来调整 |
| 新睡眠数据推送 | `trends` + `active_intervention` | 解读数据变化 + 关联干预效果 |
| 用户透露新信息 | 按话题选择 | "换了窗帘"→`lifestyle`; "最近压力大"→`psychology` |
| 用户问咖啡 | `redlines` + `cognition` | 确认红线详情 + 看认知状态决定怎么回应 |
| 子agent洞察推送 | `trends` + `active_intervention` | 关联洞察和干预效果 |
| 给建议 + 设提醒 | `redlines` + `active_intervention` + `intervention_preferences` | 避红线 + 沿方向 + 匹配用户偏好 |

---

## 多轮对话中的行为

模型在一次对话中可能多次调用 get_user_context，每次取不同的 sections。已返回的 section 内容留在对话上下文中，不需要重复拉取。

```
轮次1: 用户问"最近睡得怎么样" → 模型调 get_user_context(["trends", "sleep"])
轮次2: 用户追问"那有什么建议" → 模型调 get_user_context(["redlines", "active_intervention", "cognition"])
                                  (不重复拉 trends 和 sleep，已在上文)
轮次3: 用户说"好，试试看" → 不调用（上下文已足够）
```

---

## 子 Agent 写入规则

子 agent 更新文档时，必须：
1. 保持 section 标记格式 `# [section_key]`
2. 每个 section 内容自包含，不跨 section 引用具体数据
3. summary 与其他 section 内容一致（summary 是其他 section 的压缩）
4. 合计控制写入信息密度，每个 section 不超过其典型大小的 1.5 倍

---

## 与 v1 的对比

| 维度 | v1 全量注入 | v2 按需查询 |
|------|-----------|-----------|
| 每次必付 token | ~800 tk (两份 md) | ~80 tk (速览) |
| 画像详细度上限 | 受 800 tk 预算限制 | 不受限，section 各自可以写得更详细 |
| 简单闲聊的开销 | 和复杂场景一样 | 可能 0 额外开销 |
| 复杂场景的信息量 | 固定，可能不够 | 按需拉取 2-4 个 section，信息更精准 |
| 首轮延迟 | 无（预注入） | +1 次工具调用 |
| 红线安全性 | 全文注入，安全 | 速览含红线关键词，安全 |
