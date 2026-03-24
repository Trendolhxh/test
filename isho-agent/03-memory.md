# 03 - 记忆系统

> 一份 agent 自己维护的笔记，记录对这个用户睡眠问题的理解和改善进展

---

## 设计原则

- **一份文档，不是数据库** — agent 读写的是一份结构化笔记，不是复杂的多表结构
- **围绕睡眠问题组织** — 不记用户档案，只记"什么影响了他的睡眠、试过什么、什么有效"
- **先跑起来** — 最小可用结构，后续根据实际需要再扩展

---

## 用户画像结构

一份文档，4 个区块，由 agent 通过 `update_user_profile` 持续维护：

```yaml
# ── 背景 ──────────────────────────────────────
# 和睡眠相关的基本情况，从对话中逐步积累
background:
  age: 30
  chronotype: "night_owl"
  work: "互联网，常加班到 21-22 点"
  evening_routine: "下班后刷手机到入睡，基本没有 wind-down"
  notes: "下午必须喝咖啡（不要建议限制）"

# ── 睡眠现状 ──────────────────────────────────
# 子 agent 定期从健康数据中更新
sleep_status:
  avg_bedtime: "01:30"
  avg_deep_sleep_pct: 18
  main_issues:
    - "入睡困难：睡前手机使用"
    - "周末作息后移导致周一状态差"
  trend: "略有改善（深睡 16% → 18%）"
  updated: "2026-03-23"

# ── 干预记录 ──────────────────────────────────
# 试过什么、效果如何、为什么停了
interventions:
  - method: "晚 10 点手机放客厅"
    result: "有效但难坚持，加班日做不到"
    period: "3.20-3.22"
  - method: "限制下午咖啡"
    result: "用户拒绝"
  - method: "每晚 11 点闹钟提醒放手机"
    result: "进行中"
    started: "3.23"

# ── 不要建议 ──────────────────────────────────
# agent 的硬约束
do_not_suggest:
  - "限制咖啡"
  - "早起运动"
```

**就这么多。** 不需要 evidence 数组、confidence 评级、trend journal。Agent 是个聪明的助手，给它关键信息就够了。

---

## 读写方式

工具只需要两个操作：

| 操作 | 说明 |
|------|------|
| `get_user_profile()` | 返回完整文档。文档本身就够短（~300 token），不需要分层或分段加载 |
| `update_user_profile(path, value)` | 更新文档中的某个字段 |

**对话流程：**
```
对话开始 → get_user_profile() → 拿到全部上下文
对话中    → 发现新信息 → update_user_profile() 写入
对话结束 → 子 agent 异步更新 sleep_status（从最新健康数据）
```

---

## 子 Agent

唯一职责：定期从 `get_health_data` 拉最新数据，更新 `sleep_status` 区块。

- 每天凌晨跑一次
- 只更新 sleep_status，不动其他区块
- 主 agent 负责维护其余三个区块
