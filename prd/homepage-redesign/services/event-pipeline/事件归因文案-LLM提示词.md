> Master: ../../主文档.md §L4（事件归因 · 文案行）
> Shared: ../../shared/事件数据.md v1.4 §2.2 · ../../shared/文案长度.md
> Service: ./开发文档.md §2 阶段二
> Consumer: ../../modules/event-attribution/开发文档.md §2
> Status: Draft v1.5 · 2026-04-24（v1 立项 → v1.1 PM 四决策 → v1.2 瘦身 → v1.3 prompts 下钻分析型 → v1.4 narrative 延展叙事 + 鼓励语气 → v1.5 删【只能写】/【绝不能写】两块 + 两版解绑同指标约束 + Case 1 挪入 prompt 作 few-shot · 历史见 git log）

# 事件归因文案 · LLM 提示词

## 1. 用途与调用

为单条事件一次性生成 `narrative.day/.night` + `prompts.day/.night` 共 4 块文案。触发：冷启动首卡 / 横划切卡；同 `event.id` 幂等缓存不重复调用。

**入参字段清单**由开发按 shared/事件数据.md v1.4 + ./开发文档.md 阶段一产出自行补齐。硬约束：
① 刻意**不传 `impact`**（impact 由卡片其他槽位展示；传入会诱发电量/预算语言）；
② `headline.day` / `headline.night` 必须作为锚点传入；
③ 用户基线（HRV 14 日 / 常规入睡时刻 / 静息心率 / 睡眠时长）缺失传 null。

## 2. 完整 Prompt（系统提示词 · 中文 · 直接下发）

```
根据收到一条刚完成的健康事件，输出 narrative 与 prompts 各两版（day / night）。只输出严格 JSON，不输出任何其他文字。

【两版归因维度】
- day  版：讲这次事件对【今日精力状态】的影响——可挑这一镜头下最突出的指标切入
- night 版：讲这次事件对【晚上入睡】的影响——可挑这一镜头下最突出的指标切入

【narrative 风格】
- headline（入参 .day / .night）是规则已产的"状态定性"（≤12 字）；narrative 的任务是【围绕 headline 的延展陈述】——不是数据罗列
- 1-2 句自然语言把 headline 背后的关键数据点串起来、落到一个温和的观察结论；允许"稳稳地 / 底子不错 / 挺到位的 / 走得完整 / 干脆利落"等轻度连接修辞让句子自然可读
- 语气【带轻度鼓励色彩】：正向数据读起来轻松、负向数据温和不打击；鼓励来自数据本身的解读而非凭空打气（headline "满分" → 数据串出"难得的一夜"；headline "深睡偏少" → 承认差一点但平衡其他指标）

【prompts 设计】
- 每版 1-3 条，默认 2 条；每条 ≤ 10 字
- 每条必须围绕同版 narrative 内容展开——锚点来自 narrative 里出现的具体指标 / 时段 / 数值；禁止离题
- 问题类型**只做【下钻分析型】**：追问 narrative 指标的成因 / 机制 / 代表水平 / 扩展解读（"为什么 X？" "X 意味着什么？" "X 代表什么水平？" "X 和 Y 有关系吗？"）
- **禁止规划 / 行动 / 建议类**问题：不写"怎么做" / "要不要" / "几点 Y 合适" / "还适合再 Y 吗" / "今晚几点入睡"——规划归 Agent 正式对话，chips 只作下钻入口
- 必须是 Agent 能基于事件数据 + 用户档案回答的具体问题——禁止哲学题
- 日版下钻"今日精力状态"相关生理机制；夜版下钻"晚上入睡"相关生理机制

【长度】
- narrative 每版 ≤ 50 字（中文 / ASCII / 全角标点各按 1 字计）；1-2 句；不加 emoji / markdown / 换行

【输出 · 严格 JSON】
{
  "narrative": { "day": "...", "night": "..." },
  "prompts":   { "day": ["...","..."], "night": ["...","..."] }
}

【输出示例】
{
  "narrative": {
    "day":   "14 分钟就自然入睡，凌晨那段深睡走得完整；整晚 HRV 均值 58 ms 高出基线 9 ms，几乎没有像样的觉醒——你已经比大多数人睡的更好。",
    "night": "昨夜 HRV 整晚稳稳高出基线 9 ms，自主神经调节挺到位的；今晚入睡潜伏期预计仍能维持在 15 分钟以内的基线水平。"
  },
  "prompts": {
    "day":   ["深睡集中意味着？", "HRV 高代表什么？"],
    "night": ["HRV 影响入睡吗？", "自主神经调节是？"]
  }
}
```

## 3. 回归测试 Case · 运动 HIIT（shared/事件数据.md §3.9）

**入参要点**：subtype=vigorous / display_name=HIIT / 22min / peak_hr_pct=91% / intervals_count=4 / high_intensity_min=8 / EPOC≈90min / 核温 +0.8℃ / hours_to_bedtime=5.3h / headline.day=多段间歇的运动 / headline.night=仍可能影响入睡的运动

```json
{
  "narrative": {
    "day":   "4 段冲刺切得干脆利落，峰值冲进 Z5、间歇期又稳稳回到 130；EPOC 预计持续约 90 分钟，精力尾段预计延到 19:20。",
    "night": "核心体温还比静息高 0.8 °C，交感神经的兴奋还没完全回落；今晚入睡预计比平时慢 8-15 分钟，属于高强度训练后的正常尾声。"
  },
  "prompts": {
    "day":   ["Z5 是什么水平？", "为什么尾段延长？"],
    "night": ["核温多久才回落？", "交感神经兴奋是？"]
  }
}
```

## 4. 失败降级

LLM 失败（超时 / 拒答 / schema 错）→ 重试 1 次；仍失败则 narrative / prompts 留空；长度超限端侧按 shared/文案长度.md 硬截断 + `…`；呈现降级归 event-attribution §5.2。v1 不做敏感词过滤，人工抽样评估 §2 Do/Don't 服从率，不达标 v1.1 加过滤层。
