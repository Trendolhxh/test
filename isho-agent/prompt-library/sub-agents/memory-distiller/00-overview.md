# memory-distiller 子 Agent

> 用途：定期从 mem0 事实碎片 + 健康数据中提炼并更新用户上下文文档
> 架构：有工具调用能力的轻量 agent，3 轮 loop，总 token ≤ 10K

## 触发门控

```
三个条件必须同时满足：

1. 信息量门：自上次运行后，新增 ≥3 条 mem0 记忆
2. 时间门：距上次运行 ≥4 小时
3. 锁门：获取整合锁（简单互斥，防止并发）

兜底：每日 05:00 定时任务无视门 1 和门 2，强制执行。
```

## 工具白名单

| 工具 | 类型 | 说明 |
|------|------|------|
| `get_memories` | 占位（待开发） | 读取 mem0 新增记忆 KV 列表 |
| `get_health_data` | 复用主 agent | 查询健康指标时间序列 |
| `get_user_profile` | 复用主 agent | 加载档案 Profile 类 section |
| `get_strategy` | 复用主 agent | 加载档案 Strategy 类 section |

> 无写回工具：orchestrator 接收输出的 diff，负责写回数据库。

## Loop 流程

```
orchestrator 传入：user_id, current_date, last_update_date
                        ↓
┌─────────────────────────────────────────────────────┐
│ Turn 1  数据加载（4 个并行工具调用）                  │
│   get_memories(since=last_update_date)              │
│   get_health_data(metrics=[...], time_range=N)      │
│   get_user_profile(aspects=[all 6])                 │
│   get_strategy(aspects=[all 6])                     │
└─────────────────────────────────────────────────────┘
                        ↓ 所有工具结果返回
┌─────────────────────────────────────────────────────┐
│ Turn 2  [skill: signal-analysis]  纯推理，无工具调用  │
│   输入：新记忆 + 健康数据 + 档案锚点（非全文）        │
│   输出：结构化信号 JSON                               │
│   如无信号：输出 NO_CHANGES，loop 直接结束            │
└─────────────────────────────────────────────────────┘
                        ↓ 信号 JSON
┌─────────────────────────────────────────────────────┐
│ Turn 3  [skill: profile-merge]    纯推理，无工具调用  │
│   输入：信号 JSON + 完整 12-section 档案              │
│   输出：CHANGED sections + UNCHANGED 列表 + insight  │
└─────────────────────────────────────────────────────┘
                        ↓
           orchestrator 接收 diff，写回数据库
```

**max 3 轮**（Turn 1 是工具调用，无推理输出）。Turn 2 输出 NO_CHANGES 时提前结束，节省 Turn 3 的 ~5K token。

## Token 预算

| 组成 | Token |
|------|-------|
| 系统提示词 | ~400 |
| 工具定义（4 个） | ~500 |
| Turn 1 工具返回（新记忆 + 健康数据 + 完整档案） | ~2300 |
| Turn 2 输入累积 + 输出（信号 JSON） | ~3800 |
| Turn 3 输入累积 + 输出（diff） | ~5200 |
| **单次运行合计** | **≤ 9500 tk** |

## 关联文件

| 文件 | 说明 |
|------|------|
| `01-system-prompt.md` | Agent 身份与行为原则 |
| `02-context-loading.md` | 查询窗口策略 + 工具调用规范 |
| `03-skill-signal-analysis.md` | Turn 2 信号提取 skill |
| `04-skill-profile-merge.md` | Turn 3 档案更新 skill |
