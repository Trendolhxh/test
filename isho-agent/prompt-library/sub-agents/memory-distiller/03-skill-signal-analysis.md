# Skill: 信号提取（Turn 2）

> 在 Turn 1 数据加载完毕后，Turn 2 激活此 skill。
> 职责：从原始数据中识别哪些信息值得写入档案，以及写入哪个 section。
> 不修改档案，只输出结构化信号列表。

---

## 激活条件

Turn 1 的 4 个工具调用全部返回后，agent 进入 Turn 2，执行信号提取。

---

## 输入上下文（Turn 1 工具返回）

此 skill 可见：
- 新增记忆 KV 列表（get_memories 返回）
- 健康数据时间序列（get_health_data 返回）
- 当前档案中的 `[summary]`、`[active]`、`[redlines]`、`[cognition]`、`[trends]`（用于判断新旧矛盾）
- 完整档案的其余 sections（已在 Turn 1 加载，作为背景参考）

---

## 执行步骤

### Step 1：记忆信号扫描

遍历新增记忆列表，按 category 和内容判断每条记忆的信号价值：

| 优先级 | 类型 | 判断依据 |
|--------|------|---------|
| P0 | 用户纠正 | 记忆内容与现有档案事实矛盾，用户明确纠正旧记录 |
| P0 | 红线/拒绝 | 含"不要""别再提""没用""烦死了"等明确拒绝表述 |
| P1 | 干预反馈 | 执行结果（成功/失败/部分）、阻力、放弃原因 |
| P1 | 生活变化 | 作息改变、环境变化、新压力源、人际关系变化 |
| P2 | 常规记录 | 日常数据更新、小习惯，无矛盾、无趋势意义 |

每条信号标记：
- `target_sections`：影响哪些 section（可多个）
- `raw_quote`：用户原话（P0 必填，其他尽量保留）

### Step 2：健康数据趋势分析

分析健康数据时间序列，识别以下模式：

**值得记录的趋势（P1）：**
- 连续 ≥3 天某指标单向变化（改善或恶化）
- 干预日 vs 非干预日的系统性差异
- 周对比数据（本周 vs 上周）有明显变化（>10%）

**不值得记录（丢弃）：**
- 单日波动（次日即恢复）
- 变化幅度 <5% 且无趋势方向
- 数据缺失日（穿戴设备未佩戴）

**需标注洞察（insight 候选）：**
- 连续 ≥3 天指标恶化（非单日波动）→ 标记 `insight_candidate: true`
- 干预后指标出现显著改善（有数据印证）→ 标记 `insight_candidate: true`
- 用户画像发生重大变化（新增红线、作息模式根本性改变）→ 标记 `insight_candidate: true`

### Step 3：矛盾检测

对比新记忆/新数据与现有档案内容，逐条检查：

```
矛盾优先级规则：
1. 用户纠正 > 一切旧记忆
2. 近期事实 > 远期事实
3. 行为数据 vs 口头表述 → 不矛盾，分写不同 section
   - 数据事实 → [sleep_issues] 或 [trends]
   - 口头主观认知 → [cognition]
4. 明确拒绝 > 之前的接受
   - 旧干预从 [active] 移入 [history] 标记失败
   - 同时写入 [redlines]
```

### Step 4：NO_CHANGES 判断

如果满足以下全部条件，直接输出 `NO_CHANGES`，跳过 Turn 3：
- 新增记忆列表为空
- 健康数据无趋势信号（无 P1 及以上信号）
- 无矛盾需要处理

---

## 输出格式

### 有信号时：结构化 JSON

```json
{
  "no_signals": false,
  "signals": [
    {
      "priority": "P0",
      "type": "redline",
      "source": "memory",
      "content": "用户明确拒绝冥想干预",
      "raw_quote": "冥想对我没用，以后别再提了",
      "recorded_at": "2026-04-02",
      "target_sections": ["redlines", "active"],
      "action": "add_to_redlines + move_active_to_history"
    },
    {
      "priority": "P1",
      "type": "trend",
      "source": "health_data",
      "content": "连续3天深睡比例下降：2026-03-31 22% → 2026-04-01 19% → 2026-04-02 16%",
      "raw_quote": null,
      "recorded_at": null,
      "target_sections": ["trends", "sleep_issues"],
      "action": "update_trend + check_causation",
      "insight_candidate": true
    },
    {
      "priority": "P1",
      "type": "intervention_feedback",
      "source": "memory",
      "content": "手机放客厅干预第5天，用户反馈入睡明显变快",
      "raw_quote": "昨晚确实好一点，感觉放了手机之后不会一直刷",
      "recorded_at": "2026-04-02",
      "target_sections": ["active", "history"],
      "action": "update_active_progress"
    }
  ],
  "contradictions": [
    {
      "old_fact": "当前 [active] 包含冥想干预",
      "new_fact": "用户明确拒绝冥想（见 P0 信号）",
      "resolution": "从 [active] 移入 [history] 标记失败，写入 [redlines]"
    }
  ],
  "insight_candidates": [
    "连续3天深睡比例持续下降（22%→16%），已超阈值"
  ]
}
```

### 无信号时：直接终止

```
NO_CHANGES
```

---

## 禁止事项

- 禁止在此 skill 中修改档案内容——只识别信号，不写入
- 禁止将单日波动标记为趋势信号
- 禁止将健康数据中的正常范围波动（<5%）列为 P1 信号
- 禁止省略 `raw_quote`（P0 类信号必须保留用户原话）
