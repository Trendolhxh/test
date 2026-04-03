# 上下文加载规范

> Turn 1 的 4 个并行工具调用如何确定参数。

## 启动参数（由 orchestrator 传入）

| 参数 | 类型 | 说明 |
|------|------|------|
| `user_id` | string | 用户 ID |
| `current_date` | YYYY-MM-DD | 当前日期 |
| `last_update_date` | YYYY-MM-DD | 上次 distiller 运行日期 |
| `days_since_last_update` | int | 间隔天数（orchestrator 预计算） |

---

## 1. get_memories — 新增记忆加载

```
get_memories(
  since = last_update_date,
  limit = 50
)
```

**返回格式（orchestrator 保证输入格式）：**
```
[
  {"id": "...", "category": "redline",    "content": "用户说\"冥想对我没用\"", "recorded_at": "2026-04-02"},
  {"id": "...", "category": "routine_detail", "content": "今晚尝试11点前上床", "recorded_at": "2026-04-02"},
  ...
]
```

`recorded_at` 均为绝对日期，由 orchestrator 在写入 mem0 时标注，无需 agent 推算。

---

## 2. get_health_data — 健康数据加载

### 查询窗口策略

```python
gap = days_since_last_update

if gap <= 1:   time_range = "7d"   # 标准窗口，近期趋势
elif gap <= 3: time_range = "14d"  # 覆盖 gap 前后对比基线
elif gap <= 7: time_range = "14d"  # 双周覆盖
else:          time_range = "30d"  # 长周期趋势（最大窗口）

# 核心规则：窗口 ≥ gap × 2，最小 7d
# 确保有足够的"更新前基线"，不只是 gap 期间的 diff
```

### 常规指标（每次必查）

```
metrics = [
  "sleep_stages",        # 睡眠分期：深睡/REM/浅睡 + 入睡时长
  "sleep_debt",          # 累积睡眠债
  "sleep_consistency",   # 作息规律性
  "heart_rate",          # 静息心率
  "hrv_sdnn"             # 心率变异性
]
```

### 扩展指标（gap > 3 天时追加）

```
extra_metrics = [
  "active_energy",   # 活动量变化可能影响睡眠质量
  "screen_time"      # 与手机使用习惯关联
]
```

### 完整调用示例

```python
# gap = 2 天
get_health_data(
  metrics=["sleep_stages", "sleep_debt", "sleep_consistency", "heart_rate", "hrv_sdnn"],
  time_range="14d"
)

# gap = 5 天
get_health_data(
  metrics=["sleep_stages", "sleep_debt", "sleep_consistency", "heart_rate", "hrv_sdnn",
           "active_energy", "screen_time"],
  time_range="14d"
)
```

---

## 3. get_user_profile — 档案 Profile 类加载

```
get_user_profile(
  aspects=["routines", "sleep_strengths", "sleep_issues", "lifestyle", "psychology"]
)
```

加载全部 5 个 Profile section。[summary] 已在 system prompt 的 context 中，不需要重复请求。

---

## 4. get_strategy — 档案 Strategy 类加载

```
get_strategy(
  aspects=["redlines", "active", "history", "preferences", "cognition", "trends"]
)
```

加载全部 6 个 Strategy section。

---

## 并行调用规则

4 个工具调用在 Turn 1 **并行发出**，不依次等待。orchestrator 汇总所有结果后，统一返回给 agent 进行 Turn 2 推理。

```
Turn 1 并行：
  ┌─ get_memories(since=last_update_date)     ─┐
  ├─ get_health_data(metrics=[...], ...)       ─┤ → 汇总 → Turn 2 推理
  ├─ get_user_profile(aspects=[all])           ─┤
  └─ get_strategy(aspects=[all])              ─┘
```

---

## 占位工具：get_memories

当前 mem0 尚无对应读取工具，以下为接口规范，供后端开发参考：

```json
{
  "name": "get_memories",
  "description": "读取指定日期后新增的 mem0 记忆条目，返回格式化 KV 列表",
  "parameters": {
    "type": "object",
    "properties": {
      "since": {
        "type": "string",
        "description": "起始日期（含），格式 YYYY-MM-DD，返回此日期及之后新增的记忆"
      },
      "limit": {
        "type": "integer",
        "description": "最大返回条数，默认 50",
        "default": 50
      }
    },
    "required": ["since"]
  }
}
```

**server-side 实现要点：**
- 从 mem0 按 `user_id` + `recorded_at >= since` 过滤
- `recorded_at` 由写入时的 orchestrator 注入，保证为绝对日期（YYYY-MM-DD）
- 按 `recorded_at` 升序排列（最旧的在前，便于 agent 理解时序）
- category 枚举同 `save_memory` 的 7 个类型
