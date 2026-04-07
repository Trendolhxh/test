# 01 - System Prompt 身份层

> 对应 Claude Code: `System Section (156 tks)` + `Doing Tasks` 系列
> 设计原则：简短声明身份 + 核心原则，不超过 500 tks

## Prompt 正文

> **运行时 prompt 正文见 [prompt-library/system/01-identity.md](./prompt-library/system/01-identity.md)**——那是模型实际看到的唯一事实来源。本文档只做设计说明，不再拷贝 prompt 正文，避免两处文本不一致。

核心原则共 4 条：目标对齐、真实生活优先、持续了解用户、可执行可反馈。每条原则的展开版见 `prompt-library/system/principles/*.md`。

> **紧跟身份层之后，orchestrator 会注入 ~80 tk 的「用户速览」（用户基本信息、红线关键词、沟通风格）。详见 [03-memory.md](./03-memory.md) 和 [04-context-assembly.md](./04-context-assembly.md)。**

## 设计说明

| 设计决策 | 理由 |
|---------|------|
| 第一句话直接声明身份和角色 | 对标 Claude Code 的 "You are Claude Code, Anthropic's official CLI..." |
| 核心原则写了 4 条而不是 10 条 | 原则太多模型会"稀释注意力"，4 条覆盖所有核心逻辑 |
| 原则 2 直接给了反面例子 | "不要因为睡得晚就建议早睡"——给 LLM 反例比正例更有效 |
| 原则 3 "解释分析逻辑"不强制 | 让模型自行判断何时解释，避免每次都产生冗长输出 |
| 原则 4 只对"行动建议"触发反馈 | 日常聊天和数据解读不需要反馈卡片，避免打扰用户 |
| 红线放在速览中而非身份层 | 红线是用户动态的，通过速览注入 system prompt，确保任何情况下都不违反 |
