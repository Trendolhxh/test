# 03 - 记忆系统

> 跨会话持久化：存什么、存在哪、什么时候写、什么时候读
> 核心思路：两层结构——完整画像（source of truth）+ 摘要（每次对话必加载）

---

## 一、Layer 2：完整用户画像（Source of Truth）

完整画像是云端持久化的结构化文档，由 agent 通过 `update_user_profile` 持续写入，
由摘要子 agent 读取并压缩。主 agent 在需要深入某个方向时按 section 按需加载。

### 字段结构

```yaml
user_profile:
  # ── 基础信息 ──────────────────────────────────
  basic_info:
    birth_date: "1995-06-15"
    gender: "male"
    height_cm: 175
    weight_kg: 72
    chronotype: "night_owl"          # 自述或推断的时型：night_owl / morning / neutral
    timezone: "Asia/Shanghai"

  # ── 生活背景 ──────────────────────────────────
  # agent 从对话中逐步积累的用户生活细节
  lifestyle:
    work:
      type: "office"                 # office / remote / hybrid / shift / student
      schedule: "10:00-19:00"        # 自述的常规工作时间
      overtime_frequency: "weekly"   # rarely / monthly / weekly / daily
      notes: "互联网行业，经常有需求变更导致加班"
    diet:
      dinner_time: "20:30"           # 通常晚餐时间
      caffeine_cutoff: null          # 用户拒绝限制咖啡，不要再建议这个方向
      alcohol_frequency: "weekly"    # rarely / weekly / daily
      notes: "周末会和朋友喝酒到比较晚"
    exercise:
      type: "none"                   # none / light / moderate / intense
      frequency: null
      notes: "说过想开始跑步但一直没开始"
    screen_time:
      bedtime_usage: "heavy"         # none / light / heavy
      primary_apps: ["短视频", "微信"]
      notes: "自述睡前刷手机是入睡困难的主因"

  # ── 睡眠模式 ──────────────────────────────────
  # 由子 agent 从健康数据中分析得出，而非用户自述
  sleep_patterns:
    weekday_avg_bedtime: "01:30"
    weekday_avg_wake_time: "08:45"
    weekend_avg_bedtime: "02:30"
    weekend_avg_wake_time: "10:30"
    avg_deep_sleep_pct: 18
    avg_sleep_debt_hours: 1.5
    consistency_score: 42            # 0-100, 子 agent 计算
    recent_trend: "slightly_improving"  # declining / stable / slightly_improving / improving
    last_updated: "2026-03-23"

  # ── 偏好与边界 ──────────────────────────────────
  # agent 必须尊重的用户偏好和拒绝方向
  preferences:
    communication_style: "direct"    # direct / gentle / humorous
    suggestion_frequency: "low"      # low / medium / high — 用户希望被建议的频率
    rejected_directions:             # 用户明确拒绝过的建议方向，不要再推
      - direction: "限制咖啡"
        reason: "下午必须靠咖啡撑着"
        date: "2026-03-18"
      - direction: "早起运动"
        reason: "早上根本起不来"
        date: "2026-03-15"
    effective_methods:               # 用户尝试过且有效的方法，优先复用
      - method: "睡前把手机放客厅"
        effectiveness: "partial"     # effective / partial
        note: "做到的那两天确实睡得早了"
        date: "2026-03-20"

  # ── 活跃建议 ──────────────────────────────────
  # 当前已给出但尚未收到反馈的建议，最多保留 3 条
  active_suggestions:
    - id: "sug_003"
      date: "2026-03-23"
      content: "今晚试试 11 点把手机放到客厅，设个闹钟提醒自己"
      feedback_card_scheduled: "2026-03-24T08:00:00+08:00"
      status: "awaiting_feedback"

  # ── 建议归档 ──────────────────────────────────
  # 已 check 的建议，写入后从 active_suggestions 移除
  # 只保留最近 20 条，更早的由子 agent 消化进 preferences 和 sleep_patterns
  suggestion_archive:
    - id: "sug_001"
      date: "2026-03-20"
      content: "晚上 10 点后把手机放到客厅充电"
      outcome: "partially_effective"
      user_note: "做到了两天，第三天加班没做到"
      archived_at: "2026-03-22"
    - id: "sug_002"
      date: "2026-03-18"
      content: "下午 2 点后不喝咖啡"
      outcome: "rejected"
      user_note: "下午必须靠咖啡撑着"
      archived_at: "2026-03-19"
```

### 字段设计说明

| 设计决策 | 理由 |
|---------|------|
| `lifestyle` 用自由 notes 字段而非纯结构化 | 用户的生活细节千变万化，结构化字段覆盖常见维度，notes 兜底非结构化信息 |
| `sleep_patterns` 由子 agent 填写 | 主 agent 不应自己算统计值——让子 agent 离线跑数据分析，主 agent 专注对话 |
| `rejected_directions` 独立为数组 | 这是 agent 行为的**硬约束**，必须高可见度，不能埋在建议归档里 |
| `effective_methods` 独立为数组 | 同理，这是**优先复用**的正面信号，需要高可见度 |
| `active_suggestions` 限制 3 条 | 避免同时给太多建议导致用户执行疲劳 |
| `suggestion_archive` 限制 20 条 | 更早的归档已被子 agent 提炼进 preferences，原始记录不再需要 |
| `chronotype` 记录时型 | 影响所有时间相关建议的锚点——对夜猫子说"11点睡"和对正常时型说完全不同 |

---

## 二、Layer 1：画像摘要（每次对话必加载）

摘要由**子 agent 定期生成**（建议每天凌晨跑一次 + 每次对话结束后触发一次），
存储为独立文档，控制在 **~500 token** 以内。

### 摘要格式

```markdown
## 用户概况
男，30 岁，互联网从业者，典型夜猫子。工作日常加班，晚餐偏晚（~20:30）。

## 当前睡眠状态
- 工作日平均入睡 01:30，起床 08:45，深睡占比 18%（偏低）
- 睡眠一致性 42/100，主要问题是周末作息大幅后移
- 近期趋势：略有改善（过去 7 天深睡占比从 16% → 18%）

## 关键洞察
- 睡前刷手机是入睡困难的核心因素（用户自述 + 数据印证）
- "手机放客厅"策略有部分效果，但加班日难以坚持
- 下午咖啡是用户的硬边界，不要建议限制

## 活跃建议
- [sug_003] 今晚 11 点手机放客厅（待反馈，卡片明早 8 点展示）

## 对话注意事项
- 用户偏好直接沟通风格，不喜欢过多铺垫
- 建议频率偏低，不要每次对话都给新建议
- 已拒绝方向：限制咖啡、早起运动
```

### 摘要生成规则

| 规则 | 说明 |
|------|------|
| 必含 `已拒绝方向` | 这是最容易违反的约束，必须在摘要中醒目呈现 |
| 必含 `活跃建议` | agent 需要知道当前有哪些建议在执行中，避免重复 |
| 必含 `近期趋势` | 让 agent 知道用户在变好还是变差，决定对话基调 |
| `关键洞察` 最多 3 条 | 子 agent 应从数据和历史对话中提炼最有行动价值的洞察 |
| 不含原始数据 | 摘要只放结论，agent 需要原始数据时调用 `get_health_data` |

### 子 Agent 运行机制

```
触发时机：
  1. 每天 05:00（用户大概率在睡觉，不会有对话冲突）
  2. 每次对话结束后异步触发（捕获当次对话产生的新信息）

输入：
  - Layer 2 完整画像
  - 最近 7 天的 get_health_data 快照
  - 上一版摘要（用于 diff 对比，决定哪些内容需要更新）

输出：
  - 新版 Layer 1 摘要（覆盖旧版）
  - 如果检测到 suggestion_archive 超过 20 条：
    提炼旧建议的规律写入 preferences，清理超量归档

Token 预算：
  - 摘要正文 ≤ 500 token
  - 子 agent 自身运行预算 ≤ 4K token（输入 + 输出）
```

---

## 三、读写流程总结

```
对话开始
    │
    ├─→ get_user_profile()           → 返回 Layer 1 摘要（~500 tk，必加载）
    │
    ├─→ get_user_profile(section=X)  → 返回 Layer 2 某段完整数据（按需）
    │                                   section 可选值：
    │                                   basic_info / lifestyle / sleep_patterns /
    │                                   preferences / active_suggestions / suggestion_archive
    │
    ├─→ update_user_profile(...)     → 写入 Layer 2 完整画像
    │                                   （摘要不直接写，由子 agent 下次运行时更新）
    │
对话结束
    │
    └─→ 异步触发子 agent → 读 Layer 2 → 生成新 Layer 1 摘要
```

---

## 四、数据生命周期

```
用户说了新信息
    → agent 调 update_user_profile 写入 Layer 2
    → 对话结束后子 agent 更新 Layer 1 摘要

用户提交反馈卡片
    → 服务端写入 active_suggestions[i].feedback
    → 服务端将该建议移入 suggestion_archive
    → 下次子 agent 运行时更新摘要

suggestion_archive 超过 20 条
    → 子 agent 提炼旧建议规律到 preferences.effective_methods / rejected_directions
    → 清理最早的归档条目

用户 6 个月没用
    → 下次回来时子 agent 重新跑一遍，摘要标注"长期未活跃，数据可能过时"
```
