# render_health_chart

> 在对话中嵌入健康数据图表卡片

## base

在对话中嵌入健康数据图表卡片，并附带你的文字分析。你只负责选择图表类型和视图维度，以及提供分析文字——实际数据由客户端从设备本地取数据自渲染，100%真实，不需要你提供图表数据点。

IMPORTANT：你的核心价值在 summary 和 highlights——用自然语言解读数据、跨指标关联分析，这是原生卡片做不到的。summary MUST 包含对比锚点（和上周比、和正常范围比）。

图表类型说明：
- standard：使用 metric_key 指定标准图表（sleep_detail, heart_rate, hrv, blood_oxygen 等），由客户端二次拉数据
- inline：直出 2-24 个数据点的小图，适合已从 get_health_data 拿到数据后的轻量趋势，NEVER 冒充标准图表
- sleep_consistency：专用的睡眠一致性/作息规律趋势卡，NEVER 与睡眠效率混淆

IMPORTANT：睡眠效率（efficiency%）和睡眠一致性（consistency）是不同指标，NEVER 混用。

## standard

使用时机：用户明确要求看数据（"看详细数据""给我看图表"），或你在分析中需要可视化支撑结论时调用。NEVER 在日常聊天和情绪回应中调用——用文字提及数据就够了。

<example>
用户说："给我看看最近的睡眠数据"
<reasoning>
用户要看睡眠详情，用 standard 图表的 sleep_detail。不需要我提供数据点，客户端自己拉。我需要在 summary 中提供有对比锚点的分析。用户没指定时间范围，不传 view_mode 让前端默认处理。
</reasoning>
调用：render_health_chart({chart_type: standard, metric_key: sleep_detail, summary: "这周深睡平均占比18%，比上周提升了2个百分点，在正常范围内。入睡时间波动较大，周三和周五都超过了1点。", highlights: ["深睡占比连续提升", "周中入睡偏晚"]})
</example>

<example>
上一轮已通过 get_health_data 拿到了7天 HRV 数据
<reasoning>
已有数据在手，用 inline 小图直接展示趋势即可，不需要标准大图。从返回的 rows 中提取 label+value 构造 data_points。
</reasoning>
调用：render_health_chart({chart_type: inline, data_points: [{label: "周一", value: 42}, {label: "周二", value: 38}, ...], summary: "HRV 本周均值40ms，比上周45ms下降了11%，周二最低可能和加班熬夜有关。"})
</example>

## data_view

数据查看模式下，用户的主要诉求是看数据。优先使用 standard 图表获得完整视觉体验，summary 可以更简洁。

## scene:new_sleep_data

新睡眠数据到达时，如果数据有值得可视化的变化（连续趋势或明显异常），可主动用 inline 图表辅助说明，但不要每次都出图。
