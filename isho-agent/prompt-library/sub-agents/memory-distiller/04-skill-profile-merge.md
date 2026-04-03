---
name: memory-distiller/profile-merge
description: >
  Turn 3 skill：根据 Turn 2 的信号 JSON，精确更新档案受影响的 sections，输出差量格式。
  Turn 2 输出 no_signals=false 时激活。
  不做分析判断——信号已在 Turn 2 确定，此 skill 只负责写入。
allowed-tools: none
version: 1.0.0
---

# 档案更新

## Context

Turn 2 已完成信号识别，输出结构化 JSON（`signals` + `contradictions` + `insight_candidates`）。Turn 3 的任务是按信号精确更新档案的受影响 sections，其余 sections 原样列入 UNCHANGED，不做任何改动。

**可见上下文：**
- Turn 2 输出的信号 JSON
- 完整 12-section 档案（Turn 1 已加载）
- `current_date`（来自启动参数）

## Instructions

### 1. 确定受影响的 sections

从信号 JSON 中收集所有 `target_sections`，去重后得到需要更新的 section 列表。未在列表中的 section 原样输出到 UNCHANGED，不做任何改动。

### 2. 逐 section 执行更新

对每个受影响的 section 依次执行以下操作：

**去重**
新信号与现有内容表达同一事实时，合并为一条，不追加重复。判断标准：相同主体 + 相同行为/属性 + 时间范围重叠。

**消矛盾**
按 Turn 2 中 `contradictions` 的 `resolution` 指令执行：删除旧事实（直接删除，不留"（已过时）"标记），写入新事实。

**干预状态流转**
当信号 `action` 包含 `move_active_to_history` 时：
1. 从 `[active]` 中移除对应干预条目
2. 在 `[history]` 中新增一条，格式：
   ```
   YYYY-MM-DD~YYYY-MM-DD  干预名称  结果：失败/成功/部分  学习：{一句话}
   ```
3. `[history]` 超过 10 条时，删除最旧的一条

**日期绝对化**
所有时间引用使用 YYYY-MM-DD。新写入内容从 `current_date` 和记忆的 `recorded_at` 推算，不使用"昨天""最近"等相对表述。

**归因链更新**
当新信号揭示新的因果关系时，更新 `[sleep_issues]` 的归因链：
```
格式：睡眠时长不足 ← 上床过晚 ← 刷手机 ← 没有 wind-down
用 ← 符号连接，原因在右，结果在左
```

### 3. 重建 [summary]

**最后执行**，在其他 11 个 section 更新完毕后重建 summary：
- 从更新后的全文中提取最关键的信息压缩
- 格式：`{年龄}岁{性别}/{职业}/{睡眠类型}/{居住} | 核心问题:{...} | 阶段:{...} | 红线:{...} | 沟通:{...}`
- 控制在 ~80 token
- 仅包含其他 section 中已有的信息，不添加 summary 独有内容

### 4. 预算检查

检查更新后文档的 token 估算：
- `[summary]` 超过 80 token → 压缩，保留最关键信息
- Profile 类合计超过 500 token → 裁剪密度最低的 section 中的冗余内容
- Strategy 类合计超过 500 token → 优先保留 [redlines] 和 [active]，其余按时效性裁剪
- 总计控制在 1,100 token 以内

### 5. 洞察判断

遍历 Turn 2 的 `insight_candidates`：
- 如有候选项，选择最重要的一条生成 `insight` 字段（一句话）
- 多个候选项时，优先级：持续恶化 > 干预显效 > 画像重大变化
- 日常小波动不生成 insight

## Output Format

### 有变化时

```
CHANGED:
# [redlines]
{完整更新后的 redlines section 内容}

# [active]
{完整更新后的 active section 内容}

# [history]
{完整更新后的 history section 内容}

UNCHANGED: [routines, sleep_strengths, lifestyle, psychology, preferences, cognition]

insight: {一句话} 或 null
```

- CHANGED: 后只列出确实有内容变化的 section
- 每个 CHANGED section 输出**完整新内容**（不是 diff 格式），orchestrator 直接覆盖写入
- UNCHANGED: 后是逗号分隔的 section 名称列表，不输出这些 section 的内容
- insight: 字段在 UNCHANGED 之后

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
- 禁止在 section 内容中留下"（原内容保持不变）"等说明性文字——只输出实际内容

## Examples

**输入信号（来自 Turn 2）：**

```json
{
  "signals": [
    {"priority": "P0", "type": "redline", "content": "用户拒绝冥想", "raw_quote": "冥想对我没用，别再提了", "target_sections": ["redlines", "active"]},
    {"priority": "P1", "type": "trend", "content": "连续3天深睡下降 22%→16%", "target_sections": ["trends", "sleep_issues"], "insight_candidate": true},
    {"priority": "P1", "type": "intervention_feedback", "content": "手机放客厅第5天，入睡改善", "raw_quote": "确实好一点", "target_sections": ["active"]}
  ],
  "contradictions": [
    {"old_fact": "[active] 包含冥想干预", "new_fact": "用户拒绝冥想", "resolution": "move_active_to_history + add_to_redlines"}
  ]
}
```

**输出：**

```
CHANGED:
# [redlines]
- 咖啡（下午需要提神，硬红线）
- 早起运动（作息早起压力大，硬红线）
- 冥想（"冥想对我没用，别再提了"，2026-04-02 新增，硬红线）

# [active]
方向：减少睡前手机刺激
措施：手机放客厅，23:00 后不拿回卧室
状态：执行中，第5天
数据：入睡时长从 35min → 约 20min（用户自述，待数据验证）
下一步：继续观察 3 天后评估是否稳定

# [history]
2026-04-02  冥想 wind-down  结果：失败  学习：用户明确拒绝，认知与行为不匹配，需换方向

# [trends]
2026-03-27~2026-04-02 周对比：
深睡比例：22%（3/31）→ 19%（4/1）→ 16%（4/2），连续3天下降
入睡时长：本周均值 28min，较上周 35min 改善（干预效果待确认）

# [sleep_issues]
入睡困难 ← 睡前手机使用 ← 无 wind-down 习惯（干预中）
深睡比例下降 ← 原因待查（可能：工作压力上升 / 干预初期睡眠结构调整）

# [summary]
30岁男/产品经理/晚型人/独居 | 核心问题:入睡困难+深睡下降 | 阶段:干预初期(手机放客厅有效果) | 红线:咖啡,早起运动,冥想 | 沟通:数据驱动,不喜鸡汤

UNCHANGED: [routines, sleep_strengths, lifestyle, psychology, preferences, cognition]

insight: 连续3天深睡比例持续下降（22%→16%），与手机放客厅干预同期，原因尚不明确，建议专项跟进
```
