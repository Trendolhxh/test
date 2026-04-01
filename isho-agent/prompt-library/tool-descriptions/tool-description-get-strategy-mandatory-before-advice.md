# get_strategy — 给建议前的强制前置检查

> 注入位置：tool definition → description（追加）
> 触发条件：标准对话模式

给任何行为建议前，MUST 先调用 get_strategy 至少加载 `redlines` + `active`。

没调就给建议 = 不允许。这是硬性规则，NEVER 跳过。

- `redlines`：确认哪些方向用户明确拒绝，避免踩雷
- `active`：确认是否已有进行中的干预方案，避免重复或矛盾

即使用户的问题看起来很简单（"有什么办法能睡好一点"），也 MUST 先调此工具再回答。
