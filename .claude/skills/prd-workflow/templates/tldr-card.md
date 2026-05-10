<!--
Round 1 · TL;DR Card
插入到 prd.md 的 # TL;DR 段。≤ 200 中文字。
此时 candidate_decisions 是"候选"，Round 2 后变成"已决议"并改字段名为 decisions_made。
metrics 中数字要求 DEC 才能填的留 ?，标 depends_on。
-->

```yaml
intent: ""                              # 一句话目标，中文
non_goals:                              # 显式不做
  - ""
user_value: ""                          # 一句话用户收益
risk:                                   # 前 3 风险，中文
  - ""
metrics:                                # 怎么算成功；待 DEC 的留 ?
  - name: ""                            # 中文指标名
    target: "?"                         # 数字 + 单位，或 ?
    depends_on: []                      # 依赖的 DEC ID（如有）
candidate_decisions:                    # ≥ 3 条且 ≤ 8 条；AI 不许自己拍板
  - id: DEC-01
    question: ""                        # 中文，必须是问句
    blocks:                             # 这个决策卡住了哪些后续动作
      - ""
    needs_input_from: []                # ["产品", "算法", "设计", ...]
links:
  problem_card: ./problem-card.md
```

---

**Advance Check**：
- [ ] TL;DR YAML 段 ≤ 200 中文字
- [ ] `intent` `non_goals` `risk` `metrics` `candidate_decisions` 都非空
- [ ] `candidate_decisions` 数量 ≥ 3 且 ≤ 8
- [ ] 用户显式确认"决策点完整"
