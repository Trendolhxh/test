# 评测系统

## 概述

以**用户画像**为核心组织单位，每个画像文件包含一组评测用例。每次评测运行（run）产出 trace 和 JSON 报告，再由 `generate_full_csv.py` 汇总为一张 **30 列的完整 CSV**，覆盖「输入 → 过程 → 输出 → 评价」全链路。

CSV 每行 = 一轮 user-agent 交互。单轮 case 占 1 行；多轮对话 case 按轮次展开为多行。

## 目录结构

```
eval/
├── README.md                        # 本文件
│
│  ── 评测定义 ──
├── profile-a-night-owl.json         # 画像 A（15 case）
├── profile-b-new-user.json          # 画像 B（10 case）
├── profile-c-student.json           # 画像 C（12 case）
├── profile-d-good-sleeper.json      # 画像 D（12 case）
├── user-contexts/                   # 注入 system prompt 的用户速览
│   └── profile-{a,b,c,d}.yaml
│
│  ── 评分器 ──
├── graders/
│   ├── rules.json                   # 确定性规则（全局 + case 专属）
│   └── deterministic.py             # 确定性检查器
│
│  ── 脚本 ──
├── run_eval.py                      # 评测主入口：跑 agent → 收 trace → 打分
├── generate_full_csv.py             # 汇总生成完整 CSV
│
│  ── 产出 ──
├── traces/                          # Agent 运行 trace
│   └── {run_id}_{case_id}.json
└── reports/
    ├── {run_id}.json                # 评测原始结果
    └── {run_id}_full.csv            # 完整 CSV 报告（30 列）
```

## 评测流水线

```
profile-*.json + user-contexts/*.yaml
         │
         ▼
  run_eval.py ── 组装请求 → 调 agent → 收 trace
         │
         ├─→ traces/{run_id}_{case_id}.json
         │
         ├─→ 第 1 层: 确定性检查（毫秒级，零成本）
         │     规则: graders/rules.json
         │     内容: 红线词、禁止/必须工具、格式、句数
         │     硬性失败 → 直接标记 hard_fail
         │
         ├─→ 第 2 层: 效率指标（毫秒级）
         │     内容: tool call 次数、loop 轮数、token 消耗
         │
         ├─→ 第 3 层: 主观评价（可选，PM 自定义 judge prompt）
         │     维度和评分标准由 PM 按需定义
         │
         ▼
  reports/{run_id}.json
         │
         ▼
  generate_full_csv.py ── 关联 5 类数据源 → 生成 30 列 CSV
         │
         ▼
  reports/{run_id}_full.csv
```

### 分层原则

| | 确定性检查 | 效率指标 | 主观评价 |
|--|-----------|---------|---------|
| 速度 | 毫秒 | 毫秒 | 秒~分钟 |
| 成本 | 0 | 0 | API 调用费 |
| 可解释性 | 完全确定 | 完全确定 | PM 可定义 |
| 适用 | 红线、格式约束 | 资源消耗 | 语气、共情、内容 |

**快的先跑，确定性的先跑，硬性失败直接停。**

---

## CSV 列定义（30 列）

### 第 1 组：输入 (Input)

| # | 列名 | 粒度 | 来源 | 说明 |
|---|------|------|------|------|
| 1 | `profile_id` | case | profile JSON | 画像 ID（A / B / C / D） |
| 2 | `profile_name` | case | profile JSON | 画像名（如 "夜猫子上班族·干预中期"） |
| 3 | `case_id` | case | profile JSON | 用例 ID（如 A01） |
| 4 | `case_name` | case | profile JSON | 用例名 |
| 5 | `turn_index` | turn | 计算 | 当前轮次（从 1 开始，单轮 case 恒为 1） |
| 6 | `event_type` | case | event_context | 触发类型：user_message / app_open / feedback_submit / push_click |
| 7 | `event_timestamp` | case | event_context | 事件时间（ISO 8601） |
| 8 | `user_context_summary` | case | user-context YAML | 注入 system prompt 的用户速览 |
| 9 | `scene_instruction` | case | case JSON | 场景指令（app_open/push_click 等场景的额外上下文），无则空 |
| 10 | `user_message` | turn | messages[] | 该轮用户消息文本。非用户发起的场景为空 |

### 第 2 组：过程 (Process)

| # | 列名 | 粒度 | 来源 | 说明 |
|---|------|------|------|------|
| 11 | `agent_loop_rounds` | turn | trace | Agent 内部循环轮数 |
| 12 | `tool_call_count` | turn | trace | 工具调用总次数 |
| 13 | `tool_calls_detail` | turn | trace | 工具调用序列（见下方格式说明） |
| 14 | `turn_input_tokens` | turn | *预留* | 该轮输入 token 数 |
| 15 | `turn_output_tokens` | turn | *预留* | 该轮输出 token 数 |
| 16 | `turn_duration_ms` | turn | *预留* | 该轮总耗时（毫秒） |
| 17 | `per_step_durations` | turn | *预留* | 各步骤耗时序列 |

> **预留列**：等 trace 格式扩展后自动填充，当前为空。

### 第 3 组：输出 (Output)

| # | 列名 | 粒度 | 来源 | 说明 |
|---|------|------|------|------|
| 18 | `response_text` | turn | trace | Agent 该轮实际回复全文 |

### 第 4 组：评价 (Evaluation)

评价列为 **case 级别**。多轮 case 中只在最后一行填充，其余行为空。

#### 4a. Guideline（用例预期）

| # | 列名 | 来源 | 说明 |
|---|------|------|------|
| 19 | `expected_tool_calls` | profile JSON | 预期工具调用描述 |
| 20 | `expected_response` | profile JSON | 预期回复行为描述 |
| 21 | `rules_applied` | rules.json | 该 case 适用的规则摘要（见下方格式说明） |

#### 4b. Guideline 满足情况（客观检查）

| # | 列名 | 来源 | 说明 |
|---|------|------|------|
| 22 | `det_pass_rate` | report | 通过率（如 12/12） |
| 23 | `det_all_passed` | report | 是否全部通过 |
| 24 | `det_hard_fail` | report | 是否硬性失败 |
| 25 | `det_failed_checks` | report | 失败项详情（分号分隔） |
| 26 | `total_token_usage` | report | 整个 case 的总 token |
| 27 | `total_duration_ms` | *预留* | 整个 case 的总耗时（毫秒） |

#### 4c. 主观评价（PM 自定义）

| # | 列名 | 来源 | 说明 |
|---|------|------|------|
| 28 | `subjective_score` | LLM Judge | PM 定义的评分输出 |
| 29 | `subjective_note` | LLM Judge | PM 定义的评语输出 |
| 30 | `subjective_raw` | LLM Judge | judge 返回的完整 JSON（PM 可自由定义维度） |

> **主观评价**不预设固定维度。PM 通过编写 judge prompt 定义评分维度和输出格式，脚本将 judge 返回值写入这 3 列。当前预留为空。

---

## 列值格式说明

### `tool_calls_detail`

紧凑箭头链，参数内联：

```
get_strategy({"aspects":["action","trends"]}) → get_user_profile({"aspects":["sleep_strengths"]}) → suggest_replies({"replies":["看详细数据","继续这样"]})
```

### `rules_applied`

全局规则 + case 专属规则的摘要：

```
全局:blacklist(8词)+no_markdown(4式) | case:tool_required(get_strategy)+blacklist_refs(redline_coffee)+must_not_be_list | severity:hard_fail
```

### `per_step_durations`（预留）

```
get_strategy:120ms → model_inference:450ms → suggest_replies:80ms → model_inference:320ms
```

---

## 多轮 case 行展开规则

一个 3 轮对话 case 在 CSV 中展开为 3 行：

| turn_index | user_message | tool_calls_detail | expected_response | det_pass_rate |
|-----------|-------------|-------------------|-------------------|---------------|
| 1 | 我想改善睡眠 | get_strategy({...}) | | |
| 2 | 加班日实在做不到 | get_user_profile({...}) | | |
| 3 | 好，那就先试试看 | set_reminder({...}) → ... | 只给一条建议... | 14/15 |

- 轮 1-2：case 级评价列为空
- 轮 3（最后一轮）：填充 guideline + 满足情况 + 主观评价

---

## 画像列表

| 文件 | 画像 | 干预阶段 | 画像详细度 | 用例数 |
|------|------|---------|-----------|-------|
| profile-a-night-owl.json | 夜猫子上班族，睡前手机 | 干预中期 | 丰富 | 15 |
| profile-b-new-user.json | 刚注册的新用户 | 零阶段 | 空/极少 | 10 |
| profile-c-student.json | 大学生，作息混乱 | 首次干预 | 中等 | 12 |
| profile-d-good-sleeper.json | 作息规律近期变差 | 长期用户 | 丰富 | 12 |

画像之间在以下维度上差异最大化：睡眠问题类型、干预阶段、画像详细程度、生活场景。

## 用法

```bash
# 运行评测
python run_eval.py                         # 全部画像
python run_eval.py --profile A             # 只跑画像 A
python run_eval.py --case A01 A12 D07      # 只跑指定 case
python run_eval.py --deterministic-only    # 只跑确定性检查

# 生成完整 CSV
python generate_full_csv.py                # 使用最新 report
python generate_full_csv.py --run-id 20260410_143200  # 指定 run
```

## 迭代流程

1. **发现问题** — 手动使用中发现 agent 回复不对
2. **加回归 case** — 把触发问题的输入加到对应画像的 cases 里
3. **加规则** — 如果问题可用关键词/工具调用判断，在 `rules.json` 新增规则
4. **修复** — 修改 system prompt 或工具定义
5. **跑 eval** — `run_eval.py` 确认修复生效 + 无回归
6. **生成 CSV** — `generate_full_csv.py` 输出完整报告，对比新旧
