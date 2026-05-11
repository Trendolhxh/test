<!--
Round 1 · TL;DR Card · 嵌入 prd.md 的 # TL;DR 段
关键规则：
  - ≤ 200 中文字
  - product_shape 必填（形态锚点）
  - metrics 可选；省略时 deviations 须留痕
  - decisions_made 只能 [{id, tag}]，禁止塞长描述
  - 长内容（决议详情、辩论过程）一律去 ADR/prd.md 正文
-->

```yaml
intent: ""                              # 一句话目标，中文
product_shape: ""                       # ⚠️ 必填：形态锚点
                                        # 例："参考 OURA Readiness 二级页的 Contributors 归因结构"
                                        # 例："在 App 首页精力卡的下钻位"
                                        # 例："类似 Apple Health 趋势页"
non_goals:                              # 显式不做
  - ""
user_value: ""                          # 一句话用户收益
risk:                                   # 前 3 风险
  - ""
metrics: []                             # 可选；省略时 deviations 须留痕
                                        # 设置时：[{name: "中文指标名", target: "数字+单位 或 ?"}]
candidate_decisions:                    # Round 1 时，3-8 条；AI 不许自己拍板
  - id: DEC-01
    question: ""                        # 中文问句
    blocks: []                          # 卡住的后续动作
    needs_input_from: []                # ["产品", "算法", "设计", ...]
decisions_made: []                      # Round 2 后填；仅允许 {id, tag}
                                        # 例：[{id: DEC-01, tag: "4 档评价"}]
                                        # 禁止塞详细决议内容（去 ADR）
deviations:                             # 故意跳过的流程项
  - {item: "", reason: ""}              # 例：{item: "metric", reason: "基础功能页面无独立指标"}
```

---

**Advance Check**：
- [ ] TL;DR ≤ 200 中文字
- [ ] `product_shape` 非空
- [ ] `intent` `non_goals` `risk` 都非空
- [ ] `candidate_decisions` ∈ \[3, 8]
- [ ] §1 背景叙事段 ≥ 150 字已写
- [ ] 用户显式确认"决策候选完整"
