# get_strategy

> 了解该怎么做

## base

了解该怎么做。加载和用户合作的策略信息：什么不能碰、当前在推什么干预、用户的认知水平和误区。用于给建议、回应反馈卡、决定是否引导认知、规划下一步。

IMPORTANT：给任何行为建议前，MUST 先调此工具至少加载 redlines + active。没调就给建议 = 不允许。这是硬性规则，NEVER 跳过。

各 aspect 使用场景：
- redlines：要给建议前确认边界（哪些方向绝对不能提）
- active：涉及当前干预的任何对话（反馈卡回收、新数据关联干预效果、推送点击）
- history：需要参考过去尝试过什么（当前干预无效需要换方向）
- preferences：要设计新的干预方案（用户接受什么类型的方法）
- cognition：用户说了和睡眠认知相关的话、或需要决定怎么解释（"周末补回来就行了"）
- trends：需要用数据说话（聊最近变化、给用户看进步）

可与 get_user_profile 并行调用。用户尚无干预方案时，active/history 返回空，此时 NEVER 凭空建议——先了解用户。

## standard

<example>
用户说："有什么办法能让我早点睡"
<reasoning>
用户在寻求行为建议。给建议前必须先确认红线（有没有用户明确拒绝的方向）和当前干预（是否已有进行中的方案）。同时加载 cognition 看用户对"早睡"的理解是否有误区。
</reasoning>
调用：get_strategy({aspects: [redlines, active, cognition]})
</example>

<example>
反馈卡回收：用户点击"没做到"
<reasoning>
用户反馈干预未执行，需要加载当前活跃干预了解具体是哪个措施，同时看 history 判断这个方向是否反复失败需要换方案。
</reasoning>
调用：get_strategy({aspects: [active, history]})
</example>

## scene:feedback_submit

反馈卡提交时，MUST 加载 active 了解当前干预详情。根据反馈结果决定是否追加 history：
- "做到了" → active 即可，用于具体肯定
- "没做到" → active + history，判断是否需要换方向

## scene:agent_insight

子 agent 标记了待推送洞察时，加载 active + trends 确认洞察与当前干预方向的关联性，避免推送与用户当前策略矛盾的内容。

## scene:new_sleep_data

新睡眠数据到达时，加载 active + trends，将最新数据与干预效果关联分析。重点关注干预日 vs 非干预日的对比。
