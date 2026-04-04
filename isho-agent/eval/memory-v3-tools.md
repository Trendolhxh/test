# 用户上下文 v3：层级拆分 + 工具设计

## 核心思路

模型调用上下文有两种意图，拆成两个工具：

```
get_user_profile     →  "这个人是谁"    → 理解用户，做出恰当回应
get_strategy         →  "我该怎么做"    → 给建议、回应反馈、引导认知
```

拆两个工具而非一个工具加 domain 参数，原因：
1. 工具描述可以精准引导模型"什么时候该调哪个"
2. 需要两类信息时可以并行调用
3. 语义更清晰——模型不需要在一个大 enum 里挑选

---

## System Prompt 中的速览（始终注入，~80 tk）

```
## 用户速览
30岁男/产品经理/晚型人/独居 | 核心问题:睡前手机→上床晚→时长不足 | 阶段:干预中期,手机放客厅试跑有效 | 红线:咖啡,早起运动 | 沟通:数据驱动,不喜鸡汤,偶尔自嘲
```

速览的职责：
- 让模型在不调任何工具时也能做基本判断（纯闲聊场景）
- 红线关键词确保任何情况下不违反
- 沟通风格确保语气一致

---

## 工具 1：get_user_profile

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

### 各 aspect 的使用场景

| aspect | 什么时候拉 | 典型触发 |
|--------|----------|---------|
| `routines` | 需要知道用户某天的作息来理解上下文 | "今天加班好累"→查加班日模式; 加班日睡眠数据→理解为什么差 |
| `sleep_strengths` | 需要肯定用户、给正面反馈 | 用户分享好消息; 数据有改善; 反馈卡"做到了" |
| `sleep_issues` | 需要理解用户问题的根因来分析或建议 | 用户问"为什么我总是睡不够"; 解读差的数据 |
| `lifestyle` | 用户提到饮食/运动/环境相关话题 | "我最近换了窗帘"; "要不要少喝咖啡" |
| `psychology` | 用户表达情绪、或需要判断怎么说不会引起反感 | "好焦虑"; 反馈卡"没做到"需要理解心理阻力 |

---

## 工具 2：get_strategy

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
          "principles",
          "cognition",
          "action",
          "redlines",
          "history",
          "trends"
        ]
      },
      "description": "要加载的方面。principles=个性化第一性原理(用户的2-3个核心杠杆及其关联); cognition=认知维度(已建立/待建立的认知+学习路径+引导触发器); action=行动维度(当前干预+原理锚点+行动偏好+下一步路径); redlines=红线与约束(明确拒绝的方向+原话+软约束); history=干预历史(最近10条,每条含结果+原理级别学习); trends=近期趋势(周对比数据+干预日vs非干预日)"
    }
  },
  "required": ["aspects"]
}
```

### 各 aspect 的使用场景

| aspect | 什么时候拉 | 典型触发 |
|--------|----------|---------|
| `redlines` | 要给建议前确认边界 | "有什么建议"; 需要确认某方向能不能提 |
| `active` | 涉及当前干预的任何对话 | 反馈卡回收; 新睡眠数据关联干预效果; 推送点击 |
| `history` | 需要参考过去尝试过什么 | 当前干预无效需要换方向; 用户问"之前试过什么" |
| `preferences` | 要设计新的干预方案 | 准备给新建议; 当前方案调整 |
| `cognition` | 用户说了和睡眠认知相关的话、或需要决定怎么解释 | "周末补回来就行了"; "几点睡有什么区别"; 数据解读时考虑怎么表达 |
| `trends` | 需要用数据说话 | 聊最近变化; 新睡眠数据推送; 给用户看进步; 子agent洞察 |

---

## 场景 → 工具调用映射

| 场景 | 调用 | 理由 |
|------|------|------|
| "今天加班好累" | 不调 或 `get_user_profile(["routines"])` | 速览已够; 想关联加班模式时查 routines |
| "我最近睡得怎么样" | `get_strategy(["trends"])` | 需要数据趋势做解读 |
| "我最近睡得怎么样"(想解读深一点) | `get_strategy(["trends"])` + `get_user_profile(["sleep_issues"])` | 趋势+问题归因，解读更有深度 |
| "有什么建议" | `get_strategy(["redlines", "action", "principles"])` | 避红线+当前干预+锚定核心杠杆 |
| 准备给新建议 | `get_strategy(["redlines", "action", "principles", "history"])` | 全面了解约束、偏好和原理方向 |
| 反馈卡: 做到了 | `get_strategy(["action", "cognition"])` + `get_user_profile(["sleep_strengths"])` | 干预详情+认知强化+肯定用户 |
| 反馈卡: 没做到 | `get_strategy(["action"])` + `get_user_profile(["psychology"])` | 干预详情+理解心理阻力 |
| 新睡眠数据推送 | `get_strategy(["trends", "action"])` | 数据趋势+关联干预效果 |
| 新睡眠数据(加班日) | `get_strategy(["trends"])` + `get_user_profile(["routines"])` | 数据+识别加班日背景 |
| 用户提到咖啡 | `get_strategy(["redlines", "cognition"])` | 确认红线+看认知状态 |
| 用户说"周末补回来" | `get_strategy(["cognition"])` | 查看这个误区的引导方向 |
| 用户表达焦虑 | `get_user_profile(["psychology"])` | 理解压力模式，决定共情方式 |
| 用户透露换了窗帘 | `get_user_profile(["lifestyle"])` | 了解环境背景做关联 |
| 子agent洞察推送 | `get_strategy(["trends", "action"])` | 关联洞察和干预效果 |
| 推送点击 | `get_strategy(["action"])` | 知道推送关联的干预 |
| 纯闲聊 | 不调 | 速览足够 |

---

## 文档 section 与工具 aspect 的映射

文档仍然是一份，用 section 标记。每个 section 对应一个 aspect，服务端按映射提取。

```
文档 section          →  工具.aspect

# [summary]           →  始终注入 system prompt
# [routines]          →  get_user_profile.routines
# [sleep_strengths]   →  get_user_profile.sleep_strengths
# [sleep_issues]      →  get_user_profile.sleep_issues
# [lifestyle]         →  get_user_profile.lifestyle
# [psychology]        →  get_user_profile.psychology
# [principles]        →  get_strategy.principles
# [cognition]         →  get_strategy.cognition
# [action]            →  get_strategy.action
# [redlines]          →  get_strategy.redlines
# [history]           →  get_strategy.history
# [trends]            →  get_strategy.trends
```

---

## 与 v2 方案的差异

| 维度 | v2（一个工具） | v3（两个工具） |
|------|-------------|-------------|
| 工具数 | 1 个 get_user_context | 2 个: get_user_profile + get_strategy |
| 语义 | "我要查用户上下文的某些部分" | "我要了解这个人" vs "我要知道怎么做" |
| 模型决策负担 | 11 个 enum 混在一起选 | 5+6 分组，按意图选工具后再选 aspect |
| 并行能力 | 一次调用 | 两个工具可并行调用 |
| sleep 粒度 | 一个 `sleep` section | 拆为 `sleep_strengths` + `sleep_issues` |
| active_intervention | 一个大 section(含下一步) | 保持为一个 `active`(方向+措施+状态+下一步都在一起,因为通常一起用) |
