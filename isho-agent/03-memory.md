# 03 - 记忆系统

> 跨会话持久化：存什么、存在哪、什么时候写、什么时候读
> 核心原则：**一切围绕"理解并改善这个人的睡眠"来组织记忆**

---

## 设计理念

Agent 的使命是帮用户获得更好的睡眠。记忆系统不是通用用户档案，而是一份**持续演化的睡眠改善知识库**。

三层组织逻辑：

```
Layer 2-A  事实层     这个人是谁、过着什么样的生活（客观，变化慢）
Layer 2-B  分析层     什么在影响他的睡眠、哪些方法有效、趋势如何（agent 的认知，持续演化）
Layer 1    摘要层     压缩视图，每次对话必加载（~500 token）
```

**为什么分析层必须在 Layer 2 而非 Layer 1？**
- 分析层记录的是 agent 对用户的**累积认知**——因果假设的建立与验证、干预效果的追踪、变化趋势的叙事
- 如果只存在 Layer 1 摘要里，每次重新生成就丢失了认知演化过程
- agent 就变成了"每次都只看到一个静态快照"的失忆助手，无法说出"你上个月试了 X 没用，后来换了 Y 有改善"这样有纵深的话

---

## 一、Layer 2-A：事实层（Context — 这个人是谁）

变化慢，主要由用户自述或设备数据填充。为分析层提供背景。

```yaml
context:
  # ── 基础信息 ──────────────────────────────────
  basic_info:
    birth_date: "1995-06-15"
    gender: "male"
    height_cm: 175
    weight_kg: 72
    chronotype: "night_owl"          # 自述或推断：night_owl / morning / neutral
    timezone: "Asia/Shanghai"

  # ── 生活场景 ──────────────────────────────────
  # 不是为了描述这个人，而是为了理解"什么生活因素可能影响睡眠"
  life_context:
    work:
      type: "office"
      schedule: "10:00-19:00"
      overtime_frequency: "weekly"
      notes: "互联网行业，需求变更频繁导致加班"
    evening_routine:
      dinner_time: "20:30"
      wind_down: "基本没有，从工作直接切换到刷手机"
      screen_time_before_bed: "heavy"
      primary_apps: ["短视频", "微信"]
    substances:
      caffeine: "daily, 下午一杯，用户拒绝调整"
      alcohol: "weekly, 周末社交"
    exercise:
      type: "none"
      notes: "说过想开始跑步但一直没开始"
    stress_sources:
      - "工作需求变更和加班"
      - "周末社交压力（喝酒晚归）"

  # ── 交互偏好 ──────────────────────────────────
  interaction:
    communication_style: "direct"
    suggestion_pace: "low"           # 用户希望被建议的频率
    boundaries:                      # agent 的硬约束——这些方向不要再提
      - direction: "限制咖啡"
        reason: "下午必须靠咖啡撑着"
        since: "2026-03-18"
      - direction: "早起运动"
        reason: "早上根本起不来"
        since: "2026-03-15"
```

---

## 二、Layer 2-B：分析层（Agent 的累积认知）

这是记忆系统的**核心**——agent 对"什么影响了这个人的睡眠"的持续理解。
由主 agent 在对话中写入，由子 agent 在离线分析后补充和修正。

### 2-B-1：睡眠影响因子图（Sleep Impact Model）

Agent 逐步建立的因果认知：哪些因素影响这个用户的睡眠，影响方向和强度如何。

```yaml
sleep_impact_model:
  # 每个因子是 agent 识别到的一个影响睡眠的变量
  # 随着数据积累，confidence 和 impact 会被子 agent 更新
  factors:
    - id: "factor_01"
      name: "睡前手机使用"
      category: "behavior"           # behavior / substance / emotion / environment / schedule
      impact: "negative"             # positive / negative / mixed
      strength: "strong"             # weak / moderate / strong
      confidence: "high"             # low / medium / high
      evidence:
        - type: "self_report"
          detail: "用户自述刷手机是入睡困难的主因"
          date: "2026-03-15"
        - type: "data_correlation"
          detail: "手机放客厅的两天，入睡时间提前 45min，深睡占比 +3%"
          date: "2026-03-22"

    - id: "factor_02"
      name: "周末作息后移"
      category: "schedule"
      impact: "negative"
      strength: "moderate"
      confidence: "medium"
      evidence:
        - type: "data_pattern"
          detail: "周一睡眠质量评分比周四低 15%，社交时差效应明显"
          date: "2026-03-23"

    - id: "factor_03"
      name: "加班 / 工作压力"
      category: "emotion"
      impact: "negative"
      strength: "moderate"
      confidence: "medium"
      evidence:
        - type: "correlation"
          detail: "加班日入睡延迟平均 30min，可能与心理激活有关"
          date: "2026-03-21"
        - type: "self_report"
          detail: "用户说加班后脑子停不下来"
          date: "2026-03-19"

    - id: "factor_04"
      name: "周末饮酒"
      category: "substance"
      impact: "negative"
      strength: "weak"
      confidence: "low"
      evidence:
        - type: "data_pattern"
          detail: "样本太少（3 次），饮酒后深睡占比降低但未达显著"
          date: "2026-03-23"
      notes: "需要更多数据确认。用户没拒绝讨论这个话题，但也没主动关注。"
```

**设计说明：**
- 因子不是预设的固定列表，而是 agent 在交互过程中**发现和验证**的
- `evidence` 数组记录了这个认知是怎么建立起来的——数据支撑、用户自述、还是 agent 假设
- `confidence` 会随着新数据和用户反馈更新，这就是"认知演化"的具体载体
- 子 agent 可以基于新数据自动调整 strength 和 confidence，并追加 evidence

### 2-B-2：干预追踪（Intervention Tracker）

比"建议归档"更有结构——每个干预记录了**完整的尝试-反馈-效果链**。

```yaml
interventions:
  # ── 活跃干预（当前正在进行的） ──────────────
  active:
    - id: "int_003"
      started: "2026-03-23"
      method: "每晚 11 点手机放客厅"
      targets_factor: "factor_01"         # 对应影响因子
      status: "awaiting_feedback"
      feedback_card_at: "2026-03-24T08:00:00+08:00"

  # ── 已结束干预（有结果的） ──────────────────
  completed:
    - id: "int_001"
      period: "2026-03-20 → 2026-03-22"
      method: "晚上 10 点后手机放客厅充电"
      targets_factor: "factor_01"
      outcome: "partially_effective"
      measured_effect: "执行的 2 天入睡提前 45min，深睡 +3%"
      barrier: "加班日无法坚持"
      user_note: "做到了两天，第三天加班没做到"
      next_action: "迭代为 int_003，增加闹钟提醒机制"

    - id: "int_002"
      period: "2026-03-18 → 2026-03-19"
      method: "下午 2 点后不喝咖啡"
      targets_factor: null                # 用户直接拒绝，没有对应因子
      outcome: "rejected"
      user_note: "下午必须靠咖啡撑着"
      next_action: "已记入 boundaries，不再推荐此方向"
```

**设计说明：**
- `targets_factor` 连接干预与影响因子——agent 可以追溯"我为什么推荐这个方法"
- `measured_effect` 记录量化效果，不是模糊的"有用/没用"
- `barrier` 记录执行障碍——下次推荐同方向时需要解决这个障碍
- `next_action` 记录这次干预产生的后续动作，体现"一个方法的迭代过程"
- active 最多 3 条，completed 保留最近 15 条，更早的提炼进影响因子图

### 2-B-3：趋势日志（Trend Journal）

按时间记录的关键变化节点，让 agent 能讲出用户的"改善故事"。

```yaml
trend_journal:
  # 子 agent 每周生成 1 条，重大变化时额外生成
  # 最多保留 12 条（约 3 个月），更早的压缩进 summary_of_journey
  entries:
    - week: "2026-W11"                 # 3.10 - 3.16
      sleep_score_avg: 52
      key_observation: "baseline 周。入睡平均 01:45，深睡 16%。识别出手机使用和周末作息后移为主要影响因素。"
      milestone: null

    - week: "2026-W12"                 # 3.17 - 3.23
      sleep_score_avg: 56
      key_observation: "尝试手机放客厅，执行 2/7 天，执行日效果明显。整体略有改善。"
      milestone: "首次干预有正面效果"

  # 更早期的旅程摘要（由子 agent 压缩而来）
  summary_of_journey: |
    用户 2026-03 开始使用。初始状态：典型夜猫子，平均入睡 01:45，
    深睡占比 16%。核心问题是睡前手机使用和周末作息后移。
    第一个有效干预是"手机放客厅"，但加班日难以坚持。
```

**设计说明：**
- 这是 Layer 1 摘要里"近期趋势"的数据来源，但比摘要保留了**时间纵深**
- `milestone` 标记重要节点——agent 可以在对话中引用："你还记得两周前第一次试手机放客厅那次吗？"
- `summary_of_journey` 是超过 12 周的旧条目的压缩，确保即使用了一年，agent 仍然知道"从哪里开始的"

---

## 三、Layer 1：摘要层（每次对话必加载）

摘要是 Layer 2 全部内容的压缩视图，由子 agent 生成，控制在 **~500 token**。

### 摘要格式

```markdown
## 这个人的睡眠故事
男，30 岁，互联网从业者，典型夜猫子。使用 2 周。
核心问题：睡前手机 + 周末作息后移。首个有效方向：手机放客厅（加班日是障碍）。

## 当前状态
- 睡眠评分趋势：52 → 56（略有改善）
- 工作日入睡 01:30，深睡 18%（偏低）
- 关键改善点：执行干预的日子效果明显，问题在于坚持性

## Agent 当前认知
- [高确信] 睡前手机是入睡困难的核心因素（数据 + 自述双重印证）
- [中确信] 周末作息后移导致周一睡眠质量下降（社交时差效应）
- [中确信] 加班日心理激活延迟入睡（自述 + 数据弱相关）
- [低确信] 周末饮酒可能影响深睡（样本不足）

## 当前干预
- [int_003] 每晚 11 点手机放客厅 — 待反馈（明早 8 点展示卡片）
- 下一步方向：如果 int_003 反馈正面，考虑解决加班日的坚持性问题

## 硬约束
- 不建议：限制咖啡、早起运动
- 沟通风格：直接，少铺垫，建议频率低
```

### 摘要生成规则

| 规则 | 说明 |
|------|------|
| 以"睡眠故事"开头 | 让 agent 立刻理解这个人的改善旅程处于什么阶段 |
| 必含 `Agent 当前认知` | 按确信度排列影响因子，agent 知道该深挖什么、该观望什么 |
| 必含 `当前干预 + 下一步` | agent 知道当前在做什么、接下来可能做什么 |
| 必含 `硬约束` | 最容易违反的约束，必须醒目呈现 |
| 不含原始数据 | 摘要只放结论和方向，需要原始数据时调用 `get_health_data` |

### 子 Agent 运行机制

```
触发时机：
  1. 每天 05:00（用户大概率在睡觉，不会有对话冲突）
  2. 每次对话结束后异步触发（捕获当次对话产生的新信息）

输入：
  - Layer 2-A 事实层 + Layer 2-B 分析层（完整）
  - 最近 7 天的 get_health_data 快照
  - 上一版摘要（用于 diff 对比，决定哪些内容需要更新）

职责：
  1. 生成新版 Layer 1 摘要（覆盖旧版）
  2. 更新 sleep_impact_model 中各因子的 confidence / strength（基于新数据）
  3. 生成本周 trend_journal 条目（如果是周末运行）
  4. 如果 completed interventions 超过 15 条：提炼旧干预的规律，清理超量条目
  5. 如果 trend_journal 超过 12 条：压缩旧条目进 summary_of_journey

Token 预算：
  - 摘要正文 ≤ 500 token
  - 子 agent 自身运行预算 ≤ 4K token（输入 + 输出）
```

---

## 四、读写流程

```
对话开始
    │
    ├─→ get_user_profile()                    → Layer 1 摘要（~500 tk，必加载）
    │
    ├─→ get_user_profile(section=X)           → Layer 2 某段详细数据（按需）
    │     section 可选值：
    │       事实层：context
    │       分析层：sleep_impact_model / interventions / trend_journal
    │
    ├─→ update_user_profile(section, data)    → 写入 Layer 2
    │     主 agent 写入场景举例：
    │       - 用户透露新的生活细节 → 写 context
    │       - 发现新的睡眠影响因素 → 写 sleep_impact_model
    │       - 给出新建议 → 写 interventions.active
    │       - 收到反馈卡片 → 更新干预状态，移入 completed
    │
对话结束
    │
    └─→ 异步触发子 agent
          → 读 Layer 2 全部 + 近 7 天健康数据
          → 更新影响因子置信度
          → 更新趋势日志
          → 生成新 Layer 1 摘要
```

---

## 五、数据生命周期

```
用户说了新信息（如"最近换了更暗的窗帘"）
    → 主 agent 判断：这可能影响睡眠环境
    → 写入 context.life_context（事实）
    → 如果有足够信息，可在 sleep_impact_model 新增因子（初始 confidence: low）
    → 对话结束后子 agent 更新摘要

数据显示某因子的影响变化（如手机放客厅连续 5 天有效）
    → 子 agent 提升 factor_01 的 confidence: high, strength: strong
    → 更新 interventions.completed 中的 measured_effect
    → 在 trend_journal 中记录 milestone

用户拒绝某个建议方向
    → 主 agent 写入 context.interaction.boundaries（硬约束）
    → 对应干预标记 outcome: rejected
    → 子 agent 确保该方向出现在摘要的"硬约束"区域

用户 3 个月没用
    → 下次回来时子 agent 重新跑分析
    → 摘要标注"长期未活跃，数据可能过时，需重新了解近况"
    → 影响因子 confidence 全部降一级
```
