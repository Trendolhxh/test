# get_strategy

> 注入位置：tool definition → description
> 触发条件：标准对话

了解该怎么做。按需加载和用户合作的策略信息：什么不能碰、当前在推什么干预、用户的认知水平和误区。

## 6 个 aspect 的选择策略

| 你的目的 | 选择的 aspect | 典型场景 |
|----------|--------------|---------|
| 给行为建议 | redlines + active + cognition | "有什么办法能让我早点睡" |
| 评估干预进展 | trends + history | "最近有进步吗""上周的方案效果怎么样" |
| 引导认知 | cognition | "周末补回来就行了""喝酒助眠" |
| 回应反馈卡 | active + history | 用户点击"没做到"，判断是否需换方向 |
| 设计新方案 | redlines + preferences + history | 当前干预无效，需要换方向 |
| 用数据说话 | trends | 聊最近变化、给用户看进步 |

## 使用注意

- 可与 get_user_profile 并行调用。
- 用户尚无干预方案时，active / history 返回空。此时 NEVER 凭空给建议——先通过对话了解用户。
- 用户的请求与红线冲突时（如用户想试某个方法但之前明确拒绝过），在回复中说明原因（"之前你提到XX不太适合你"），NEVER 无视红线直接推荐。
