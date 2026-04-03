# 上下文加载规范

> 数据加载阶段的 4 个并行工具调用如何确定参数。

## 启动参数（由 orchestrator 传入）

| 参数 | 类型 | 说明 |
|------|------|------|
| `user_id` | string | 用户 ID |
| `current_date` | YYYY-MM-DD | 当前日期 |
| `last_update_date` | YYYY-MM-DD \| null | 上次 distiller 运行日期，首次运行为 null |
| `days_since_last_update` | int \| null | 间隔天数（orchestrator 预计算），首次运行为 null |

---

## 1. get_memories — 新增记忆加载

```
get_memories(
  since = last_update_date,   // 首次运行时传 null，服务端返回全量记忆
  limit = 50
)
```

**返回格式（orchestrator 保证输入格式）：**
```
[
  {"id": "...", "category": "redline",       "content": "用户说\"冥想对我没用\"", "recorded_at": "2026-04-02"},
  {"id": "...", "category": "routine_detail","content": "今晚尝试11点前上床",    "recorded_at": "2026-04-02"},
  ...
]
```

`recorded_at` 均为绝对日期，由 orchestrator 在写入 mem0 时标注。记忆按 `recorded_at` 升序排列，P0 类（红线/拒绝/用户纠正）优先返回。

---

## 2. get_health_data — 健康数据加载

### 查询窗口策略

```python
gap = days_since_last_update

if gap is None: time_range = "30d"  # 首次运行，取长窗口建立基线
elif gap <= 1:  time_range = "7d"   # 标准窗口，近期趋势
elif gap <= 7:  time_range = "14d"  # 覆盖 gap 前后对比基线
else:           time_range = "30d"  # 长周期趋势（最大窗口）

# 核心规则：窗口 ≥ gap × 2，最小 7d，确保有足够的更新前基线
```

### 常规指标（每次必查）

```
metrics = [
  "sleep_stages",       # 睡眠分期：深睡/REM/浅睡 + 入睡时长
  "sleep_debt",         # 累积睡眠债
  "sleep_consistency",  # 作息规律性
  "heart_rate",         # 静息心率
  "hrv_sdnn"            # 心率变异性
]
```

### 扩展指标（gap > 3 天时追加）

```
extra_metrics = [
  "active_energy",  # 活动量变化可能影响睡眠质量
  "screen_time"     # 与手机使用习惯关联
]
```

---

## 3. get_user_profile — 档案 Profile 类加载

```
get_user_profile(
  aspects=["summary", "routines", "sleep_strengths", "sleep_issues", "lifestyle", "psychology"]
)
```

加载全部 6 个 Profile section，含 [summary]。

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

4 个工具调用在数据加载阶段**并行发出**，不依次等待。orchestrator 汇总所有结果后统一返回给 agent。

```
数据加载阶段（并行）：
  ┌─ get_memories(since=last_update_date)     ─┐
  ├─ get_health_data(metrics=[...], ...)       ─┤ → 汇总 → 信号分析阶段
  ├─ get_user_profile(aspects=[all 6])         ─┤
  └─ get_strategy(aspects=[all 6])            ─┘
```

---

## 占位工具：get_memories 接口规范

当前 mem0 尚无对应读取工具，接口规范如下（供后端开发参考）：

```json
{
  "name": "get_memories",
  "description": "读取指定日期后新增的 mem0 记忆条目，返回格式化 KV 列表",
  "parameters": {
    "type": "object",
    "properties": {
      "since": {
        "type": ["string", "null"],
        "description": "起始日期（含），格式 YYYY-MM-DD；null 时返回全量记忆"
      },
      "limit": {
        "type": "integer",
        "description": "最大返回条数，默认 50。P0 类（redline/correction）优先返回，不受 limit 截断",
        "default": 50
      }
    },
    "required": ["since"]
  }
}
```
