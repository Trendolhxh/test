# ADR-01 · 误报率上限定为每日 1 次

```yaml
dec_id: DEC-01
status: accepted
decided_at: "2026-05-09T11:00:00Z"
decided_by: 产品 + 算法
```

## 背景

参考竞品卸载数据，每日误报次数与卸载呈强正相关。

## 选项

A · 每日 ≤ 1 次  
B · 每日 ≤ 3 次

## 决议

采用 A。理由：克制策略优先，参考 Apple Watch / Fitbit。
