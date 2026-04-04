# get_strategy — 给建议前的强制前置检查

> 注入位置：tool definition → description（追加）
> 触发条件：标准对话模式

给任何行为建议前，务必先调用 get_strategy 至少加载 `redlines` + `action` + `principles`。

没调就给建议 = 不允许。这是硬性规则，绝不跳过。

- `redlines`：确认哪些方向用户明确拒绝，避免踩雷
- `action`：确认是否已有进行中的干预方案，避免重复或矛盾
- `principles`：确认用户的核心杠杆，确保建议锚定在第一性原理上，不脱离大方向

即使用户的问题看起来很简单（"有什么办法能睡好一点"），也务必先调此工具再回答。
