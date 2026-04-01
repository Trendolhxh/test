# save_memory

> 将对话中捕获的用户新事实写入记忆

## base

将在对话中捕获的用户新事实写入记忆。当用户告诉你生活细节、表达偏好或拒绝、反馈干预执行情况时调用。

ALWAYS 存的：用户陈述的客观事实、生活变化、偏好表达、干预反馈、认知表达或误区、环境/设备变化。
NEVER 存的：简单确认（好的/知道了）、你已知的信息、纯情绪感叹（除非揭示了新的生活事实）、你自己的分析或推测。

IMPORTANT：静默操作——NEVER 说"我记下了"或任何类似的确认。写入的内容会在下次子 agent 运行时提炼进用户上下文文档。

## standard

与 record_event 的区别——save_memory 是自然语言事实碎片（喂给子 agent 做提炼），record_event 是结构化行为记录（落库、可查询）。用户说"我中午喝了杯咖啡"→ 调 record_event；用户说"我最近不太想喝咖啡了"→ 调 save_memory。NEVER 混用两者。

<example>
用户说："我最近换了工作，现在每天通勤要两个小时"
<reasoning>
这是新的生活变化，会影响作息模式和精力管理策略。属于 routine_detail 类别。记录客观事实，不加分析。
</reasoning>
调用：save_memory({content: "用户最近换了工作，每天通勤需要两个小时", category: routine_detail})
</example>

<example>
用户说："别再让我试冥想了，我真的做不到"
<reasoning>
用户明确拒绝了一个干预方向，这是重要的偏好信息，需要记录以避免未来重复推荐。属于 preference 类别。
</reasoning>
调用：save_memory({content: "用户明确拒绝冥想类干预，原话：'真的做不到'", category: preference})
</example>

## onboarding

新用户引导阶段，重点捕获：作息模式、睡眠诉求、生活习惯、职业信息等基础画像信息。每条信息都值得记录，这是构建用户画像的关键窗口。
