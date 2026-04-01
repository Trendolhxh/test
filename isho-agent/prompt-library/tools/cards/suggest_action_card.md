# suggest_action_card

> 展示行动决策卡片

## base

展示一张行动决策卡片，包含标题和若干可点击动作按钮。当你给完分析或建议后，需要用户明确选择下一步时使用。

适用场景：给出多个可能的行动方向让用户选择、或需要用户做明确的是/否决定时。
不适用：日常聊天、数据解读（用 suggest_replies 即可）。

## standard

与 suggest_replies 的区别：suggest_replies 是轻量的文字快捷按钮（用户点击=发送文字）；suggest_action_card 是更正式的决策卡片（有标题、有结构），用于需要用户认真考虑的选择。
