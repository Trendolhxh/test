---
name: memory-distiller/profile-merge
description: >
  档案更新：按信号提取的结果，精确更新档案受影响的 sections，输出差量格式供 orchestrator 写回。
  信号提取产出有效信号（no_signals=false）后执行。
  信号提取输出 NO_CHANGES 时不执行——没有信号就没有可更新的内容。
allowed-tools: none
version: 1.0.0
---

# 档案更新

## Context

信号提取已完成，产出了结构化信号 JSON（`signals` + `contradictions` + `insight_candidates`）。此 skill 的任务是按信号精确更新档案受影响的 sections，其余 sections 原样列入 UNCHANGED，不做任何改动。

不做分析判断——信号已在提取阶段确定，此 skill 只负责写入。

## Instructions

### 1. 确定受影响的 sections

从信号 JSON 中收集所有 `target_sections`，去重后得到需要更新的 section 列表。未在列表中的 section 原样输出到 UNCHANGED，不做任何改动。

### 2. 逐 section 执行更新

对每个受影响的 section 依次执行：

**去重**：新信号与现有内容表达同一事实时，合并为一条，不追加重复。判断标准：相同主体 + 相同行为/属性 + 时间范围重叠。

**消矛盾**：按 `contradictions` 的 `resolution` 指令执行。删除旧事实（直接删除，不留"（已过时）"标记），写入新事实。

**干预状态流转**：当信号 `action` 包含 `move_action_to_history` 时：
1. 从 `[action]` 的"当前干预"中移除对应条目
2. 在 `[history]` 中新增一条：`{干预名称}({日期范围}): {结果概述}\n  学习: {对策略的启示}[{关联杠杆}]`
3. `[history]` 超过 10 条时，删除最旧的一条

**认知状态流转**：当信号 `action` 包含 `move_to_established` 时：
1. 将对应认知点从 `[cognition]` 的"待建立"移至"已建立"
2. 移除对应的引导触发器（目标已达成）
3. 如有下一优先级的待建立认知，可更新引导策略

**日期绝对化**：所有时间引用使用 YYYY-MM-DD，从 `current_date` 和记忆的 `recorded_at` 推算，不使用"昨天""最近"等相对表述。

**归因链更新**：新信号揭示新因果时，更新 `[sleep_issues]` 归因链格式：`结果 ← 原因 ← 根因`（← 连接，原因在右）。

**P2 信号处理**：token 预算充裕时处理；Profile 类接近 500 token 上限时跳过 P2 信号。

### 3. 重建 [summary]

**最后执行**，在其他 11 个 section（6 Profile + 5 Strategy，不含 summary 本身）更新完毕后重建：
- 格式：`{年龄}岁{性别}/{职业}/{睡眠类型}/{居住} | 核心问题:{...} | 阶段:{...} | 红线:{...} | 沟通:{...}`
- 控制在 ~80 token
- 只包含其他 section 中已有的信息，不添加独有内容

### 4. 预算检查

- `[summary]` 超过 80 token → 压缩，保留最关键信息
- Profile 类合计超过 500 token → 裁剪密度最低的 section 中的冗余内容
- Strategy 类不设 token 上限（get_strategy 按需动态加载），但仍应保持紧凑避免冗余

### 5. 洞察判断

遍历 `insight_candidates`，选最重要的一条生成 `insight` 字段（一句话）。优先级：持续恶化 > 干预显效 > 画像重大变化。日常小波动不生成 insight。

## Output Format

### 有变化时

CHANGED sections 按 12-section 声明顺序输出（Profile 类先，Strategy 类后），[summary] 始终最后（需在其他 sections 更新完毕后重建）：

```
CHANGED:
# [sleep_issues]
{完整更新后的内容}

# [redlines]
{完整更新后的内容}

# [action]
{完整更新后的内容}

# [history]
{完整更新后的内容}

# [trends]
{完整更新后的内容}

# [summary]
{重建后的内容}

UNCHANGED: [routines, sleep_strengths, lifestyle, psychology, cognition]

insight: {一句话} 或 null
```

规则：
- CHANGED 只列出确实有内容变化的 section
- 每个 CHANGED section 输出**完整新内容**（不是 diff），orchestrator 直接覆盖写入
- UNCHANGED 后是逗号分隔的 section 名称列表，不输出内容
- insight 字段在 UNCHANGED 之后

### 无变化时

```
NO_CHANGES
```

## Guardrails

- 只更新 CHANGED 中的 section，UNCHANGED 中的 section 禁止改动（即使发现措辞可以优化）
- 禁止在 [summary] 中写入其他 section 未提及的信息
- 禁止丢弃 [redlines] 中的任何条目
- 禁止用模糊表述替代具体数值
- 禁止在输出中保留相对时间词（"最近""昨天""上周"）
- 禁止在 section 内容中留下"（原内容保持不变）"等说明性文字

## Examples

**输入信号：**

```json
{
  "signals": [
    {"priority": "P0", "type": "redline", "content": "用户拒绝冥想", "raw_quote": "冥想对我没用，别再提了", "target_sections": ["redlines", "action"]},
    {"priority": "P1", "type": "trend", "content": "连续3天深睡下降 22%→16%", "target_sections": ["trends", "sleep_issues"], "insight_candidate": true},
    {"priority": "P1", "type": "intervention_feedback", "content": "手机放客厅第5天，入睡改善", "raw_quote": "确实好一点", "target_sections": ["action"]},
    {"priority": "P1", "type": "cognition_change", "content": "用户主动提到社交时差", "raw_quote": "我知道周末晚睡周一会倒时差", "target_sections": ["cognition"]}
  ],
  "contradictions": [
    {"old_fact": "[action] 包含冥想干预", "new_fact": "用户拒绝冥想", "resolution": "move_action_to_history + add_to_redlines"}
  ]
}
```

**输出：**

```
CHANGED:
# [sleep_issues]
入睡困难 ← 睡前手机使用 ← 无 wind-down 习惯（干预中）
深睡比例下降 ← 原因待查（可能：工作压力上升 / 干预初期睡眠结构调整）

# [cognition]
已建立:
  - 睡前手机影响入睡 [原理:wind-down] (认知有但行动未跟上→行动层解决)
  - 深睡的重要性 [原理:精力公式]
  - 社交时差概念 [原理:睡眠一致性] (2026-04-03 用户主动使用该概念)
待建立:
  - 酒精抑制深睡 [原理:兴奋剂管理] ← 优先级:中, 周五聚餐场景相关
引导策略:
  - 用他自己的数据做前后对比，不讲大道理
  - 触发器: 周五聚餐后深睡数据明显差时 → 用当晚vs前一晚数据引入酒精与深睡的关系

# [action]
当前干预:
  名称: 手机放客厅
  原理锚点: wind-down过渡
  措施: 手机放客厅, 23:00后不拿回卧室
  状态: 执行中(2026-03-23开始), 第5天
  数据: 入睡时长从35min→约20min(用户自述, 待数据验证)
  阻力: 加班日"补偿性娱乐"需求
偏好:
  接受: 环境改变、定时提醒、渐进式目标
  不接受: 需意志力的、大幅改作息的、冥想
  原则: 先小范围试跑, 数据证明有效再固化
下一步:
  有效路径: 继续观察3天→评估是否稳定→固化
  无效路径: 尝试手机定时锁屏工具辅助

# [redlines]
硬红线(用户明确拒绝):
  - 咖啡: "下午必须靠咖啡撑着" (2026-03-18)
  - 早起运动: "早上根本起不来" (2026-03-15)
  - 冥想: "冥想对我没用，别再提了" (2026-04-02)
软约束(建议谨慎):
  - 周五社交: 用户重视社交, 不要频繁建议减少

# [history]
- 冥想wind-down(04-01~04-02): 失败, 用户明确拒绝
  学习: 用户对冥想类活动接受度为零, 不可从此方向切入[wind-down]
- 手机放客厅(03-20~03-22): 部分有效, 入睡提前45min/深睡+3%, 加班日做不到
  学习: 环境设计对此用户有效[wind-down], 但加班日补偿心理是独立阻力

# [trends]
2026-03-27~2026-04-02 周对比:
  深睡比例: 22%(3/31)→19%(4/1)→16%(4/2), 连续3天下降
  入睡时长: 本周均值28min, 较上周35min改善(干预效果待确认)

# [summary]
30岁男/产品经理/晚型人/独居 | 核心问题:入睡困难+深睡下降 | 阶段:干预初期(手机放客厅有效果) | 红线:咖啡,早起运动,冥想 | 沟通:数据驱动,不喜鸡汤

UNCHANGED: [routines, sleep_strengths, lifestyle, psychology, principles]

insight: 连续3天深睡比例持续下降（22%→16%），与手机放客厅干预同期，原因尚不明确，建议专项跟进
```
