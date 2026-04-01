# show_status

> 显示进度提示

## base

在对话中显示一条进度提示。当你即将执行耗时操作（如查询数据、生成分析）时调用，让用户知道你正在工作而不是卡住了。提示会在后续回复到达后自动消失。

典型用法：先调 show_status，再调 get_health_data 或 render_health_chart。
文案用自然语言，NEVER 暴露工具名或技术术语（说"正在看你的数据"，NEVER 说"正在调用 get_health_data"）。
