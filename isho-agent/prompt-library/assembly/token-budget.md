# Token 预算

> 基于 13 个 Model-Facing 工具 + 更新后的 system prompt 片段重新估算

## 总预算分配

以 Claude Sonnet 200K 上下文为基准。精力管家是短对话场景，预留 ~10K 足够。

| 区块 | 预算 | 性质 | 来源 |
|------|------|------|------|
| ① 身份层 | ~250 tk | 固定 | system/01-identity.md |
| ② 用户速览 | ~80 tk | 按用户动态 | 子 agent 生成的 [summary] |
| ③ 样式指令 | ~200 tk | 固定 | system/03-style.md |
| ④ 工具使用总则 | ~300 tk | 固定 | system/04-tool-usage-guidelines.md |
| ⑤ 场景指令 | ~80 tk | 按事件动态，可选 | system/scenes/*.md |
| **system 合计** | **~910 tk** | | |
| ⑥ 工具定义 | ~1500 tk | 按白名单加载 | tools/**/*.json（13 个工具） |
| **system + tools** | **~2,410 tk** | | **占 200K 的 1.2%** |
| ⑦ 对话历史 + 工具结果 | ~5,000 tk | 动态 | 包含 get_user_profile/get_strategy 返回 |
| 模型输出 | ~2,000 tk | | 单次回复上限 |
| **总计** | **~9,410 tk** | | **远低于上下文上限** |

## 与旧版对比

| 指标 | 旧版（02-tools.md 9 工具） | 新版（13 工具） | 变化 |
|------|---------------------------|----------------|------|
| system prompt | ~530 tk | ~910 tk | +380 tk（新增工具总则）|
| 工具定义 | ~1,000 tk | ~1,500 tk | +500 tk（多 4 个工具）|
| system + tools | ~1,530 tk | ~2,410 tk | +880 tk |
| 占 200K 比例 | 0.77% | 1.2% | 仍然极低 |

增加的 ~880 tk 换来了：
- 更精准的工具语义（卡片按场景拆分）
- 新增 record_event（行为记录）和 analyze_food_sleep_impact（食物分析）
- 工具使用总则（减少误调用）

## 各工具 token 估算

| 工具 | 预估 tk | 说明 |
|------|---------|------|
| get_health_data | ~200 | 14 个 metrics 枚举 + 丰富的 description |
| get_user_profile | ~150 | 5 个 aspects + 使用场景说明 |
| get_strategy | ~180 | 6 个 aspects + 强制前置检查说明 |
| save_memory | ~120 | 7 个 category + 存/不存规则 |
| record_event | ~120 | 4 个 event_type + 与 save_memory 区分 |
| analyze_food_sleep_impact | ~80 | 3 个参数，description 较短 |
| suggest_action_card | ~80 | 简单结构 |
| render_health_chart | ~200 | 3 种 chart_type + 12 个 metric_key 枚举 |
| suggest_sleep_adjust | ~60 | 3 个参数 |
| suggest_high_energy_window | ~50 | 3 个参数 |
| show_status | ~40 | 极简 |
| suggest_replies | ~60 | 带约束条件的 description |
| set_reminder | ~80 | 含 repeat 枚举 |
| **合计** | **~1,420 tk** | |

## 无压缩需求

精力管家是短对话场景（用户聊几句就走），典型对话 1-4 轮，不像 Claude Code 动辄几百轮。

- 总上下文消耗 ~10K，远低于 200K 上限
- 不需要设计对话压缩策略
- 不需要 ToolSearch 延迟加载机制
- 如果未来对话变长（如引入周度回顾等长对话场景），再考虑压缩
