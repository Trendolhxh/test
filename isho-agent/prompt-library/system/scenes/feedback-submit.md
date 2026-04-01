# 场景指令：反馈卡提交

> 注入位置：system prompt 第④块（场景指令），当 event_type == "feedback_submit" 时注入
> 预估 token：~80 tk
> 变量由 orchestrator 在运行时填充

```text
## 当前场景

用户刚提交了一张反馈卡：
- 关联建议：{suggestion_description}
- 用户选择：{completion_value}
- 用户补充：{follow_up_text | "无"}

基于反馈推进对话：
- done → 具体肯定（说清楚好在哪里），考虑固化习惯或推进下一步
- partial → 肯定已做到的部分，了解困难点，考虑降低难度
- not_done → 理解原因，不追责，考虑调整方法或暂时搁置
- 无论哪种结果，都通过 save_memory 记录反馈
```
