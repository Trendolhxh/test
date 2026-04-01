# get_health_data

> 注入位置：tool definition → description
> 触发条件：标准对话、数据查看模式

查询用户的健康与行为数据。支持查询今日实时值或过去 N 天的历史趋势。一次调用可查询多个指标，无需分开请求。

## 指标与时间范围

14 种可查询指标：high_energy_hours_total, high_energy_hours_remaining, sleep_stages, sleep_debt, sleep_consistency, heart_rate, resting_heart_rate, hrv_sdnn, active_energy, steps, workouts, blood_oxygen, respiratory_rate, screen_time。

4 种时间范围：today（实时值）、7d、14d、30d（每日汇总数组）。

## 按话题选指标

| 用户话题 | 推荐指标子集 |
|----------|-------------|
| 精力/疲劳 | sleep_stages + hrv_sdnn + high_energy_hours_total |
| 昨晚睡眠 | sleep_stages（today） |
| 心率/压力 | heart_rate + hrv_sdnn |
| 运动影响 | workouts + sleep_stages + hrv_sdnn |
| 作息规律 | sleep_consistency + sleep_stages |
| 综合趋势 | sleep_stages + hrv_sdnn + sleep_debt |

## 渐进式查询策略

ALWAYS 先查 7d 看趋势。发现异常再扩展到 14d 或 30d 确认是否持续性问题。一次请求多个相关指标做交叉分析，NEVER 分多次请求能在一次完成的查询。

## 返回数据为空时

某些指标返回空（用户未佩戴设备、指标不可用）时，用文字告知"这段时间的XX数据暂时没有"，NEVER 编造数据，NEVER 忽略空值继续分析。可基于其他有效指标给出有限结论。
