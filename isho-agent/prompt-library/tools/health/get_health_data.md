# get_health_data

> 查询用户的健康与行为数据

## base

查询用户的健康与行为数据。支持查询今日实时值或过去 N 天的历史趋势。一次调用可查询多个指标，无需分开请求。

## standard

使用时机：用户问起数据（"最近睡得怎么样""心率正常吗"）、需要用数据支撑分析、或需要验证干预效果时调用。

NEVER 在以下情况调用：
1. 用户只是在表达情绪（"好累啊"），先回应情绪再决定是否查数据
2. 上一轮已拉过相同指标和时间范围，直接用已有结果
3. 回答通用科普问题（"什么是HRV"），用模型知识直接答

查询策略：ALWAYS 先查 7d 看趋势，发现异常再扩展到 14d 或 30d 确认是否持续。一次请求多个相关指标（如 sleep_stages + hrv_sdnn）做交叉分析。

异常值处理：返回数据中出现极端值时，MUST 先考虑数据源问题（设备脱落、未佩戴）再做生理解释。极端值要关联用户生活事件。数据质量可疑时在回复中声明局限性。

<example>
用户说："最近总觉得没精神"
<reasoning>
用户没有指定具体指标，但描述的是精力问题。精力与睡眠质量和HRV强相关。应该拉 sleep_stages + hrv_sdnn 做交叉分析，先看7天趋势。同时拉 high_energy_hours_total 看精力量化数据。
</reasoning>
调用：get_health_data({metrics: [sleep_stages, hrv_sdnn, high_energy_hours_total], date_range: 7d})
</example>

<example>
用户说："昨晚睡得好吗"
<reasoning>
用户问的是昨晚单次睡眠，用 today 拉最近一次睡眠数据即可。sleep_stages 包含入睡时间、各分期时长，足够回答。不需要拉历史趋势。
</reasoning>
调用：get_health_data({metrics: [sleep_stages], date_range: today})
</example>

## data_view

用户进入数据查看模式，专注于展示数据。配合 render_health_chart 使用，先拉数据再决定图表类型。查询策略同标准对话。

## scene:new_sleep_data

新睡眠数据到达时，优先拉 sleep_stages(today) 获取最新一夜数据，再与 7d 趋势对比发现变化。关注入睡时间、深睡占比、总时长三个核心指标的变化方向。
