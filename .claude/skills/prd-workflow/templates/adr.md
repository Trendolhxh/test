<!--
ADR · Architecture Decision Record · 单条决策一份
文件名：ADR-{DEC-ID 数字部分}.md，例如 DEC-02 → ADR-02.md
落在 specs/{slug}/adr/ 下
-->

# ADR-{{NUMBER}} · {{中文决策标题}}

```yaml
dec_id: DEC-{{NUMBER}}
status: accepted              # proposed | accepted | superseded
decided_at: {{ISO-8601}}
decided_by: {{人名 / 角色}}
supersedes: []                # 如果替换了旧 ADR，填旧 ID
links:
  prd: ../prd.md
  sketch: ../ui/round-1.5-DEC-{{NUMBER}}.html  # 如有
```

## 背景与问题

> 中文叙述。为什么需要做这个决策？影响哪些 AC、模块、用户体验？

## 选项

### A · {{方案 A 名}}
- 优势：
- 劣势：
- 影响：

### B · {{方案 B 名}}
- 优势：
- 劣势：
- 影响：

## 决议

**采用：方案 {{X}} · {{方案名}}**

理由（中文，3–5 行）：

## 后果与跟进动作

- 触发的 AC 变更：[AC-XX, AC-YY]
- 触发的契约变更：[api / events / algorithm / hardware]
- 后续监控/复盘动作：

## 反对意见与风险（来自评审）

> 留白：如果有人反对但被否决，记录在这里，方便 6 个月后复盘。
