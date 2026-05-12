<!--
示例 PRD · 用于自检 lint 脚本
-->

---
feature: heart-rate-alert
version: v0.2
status: drafting
---

# 心率告警通知

# TL;DR

```yaml
intent: 静息高心率持续触发本地告警，引导用户进入静息检测
non_goals:
  - 不做心律失常诊断
  - 不在用户不戴表时弹通知
user_value: 帮助用户更早察觉潜在心率异常
risk:
  - 误报会让用户卸载
  - 运动场景刷屏
  - 低光场景信号失准
metrics:
  - name: 通知点击率
    target: ">=25%"
  - name: 误报率
    target: "<=每日1次"
candidate_decisions:
  - id: DEC-01
    question: 误报率上限定多少
    blocks: [AC 阈值]
    needs_input_from: [产品, 算法]
  - id: DEC-02
    question: 通知形态用全屏卡片还是表盘小红点
    blocks: [UI 实现]
    needs_input_from: [设计, 产品]
decisions_made:
  DEC-01: A
  DEC-02: B
```

# 1. 背景

略。

# 2. 决策记录

| ID | 问题 | 决议 | ADR |
|---|---|---|---|
| DEC-01 | 误报率上限 | A · 每日 ≤ 1 次 | adr/ADR-01.md |
| DEC-02 | 通知形态 | B · 全屏卡片 | adr/ADR-02.md |
