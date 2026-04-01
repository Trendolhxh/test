# show_status

> 注入位置：tool definition → description
> 触发条件：标准对话、数据查看模式、新用户引导

在对话中显示一条进度提示。当你即将执行耗时操作时调用，让用户知道你正在工作而不是卡住了。提示会在后续回复到达后自动消失。

## 典型用法

在调用 get_health_data 或 render_analysis_card 前调用。

## 文案要求

用自然语言，NEVER 暴露工具名或技术术语。

- 正确："正在看你过去一周的睡眠数据..."
- 正确："让我看看最近的变化..."
- 错误："正在调用 get_health_data..."
- 错误："正在查询 sleep_stages 指标..."
