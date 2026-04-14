# Agent 评测系统 (Eval System) PRD

> 文档版本：v1.0 | 创建日期：2026-04-14
> 状态：**正式 PRD**
> 所属模块：精力管家 Agent · 质量保障

---

## 一、功能定义

### 1.1 核心定义

精力管家 Agent 的自动化评测系统。每次 Agent 的 prompt、工具定义或策略逻辑变更后，通过批量运行预设用例、收集 trace、分层打分，生成一张信息完整的 CSV 报告，覆盖「输入 → 过程 → 输出 → 评价」全链路。

核心目标：**让每次变更的质量影响可量化、可对比、可回溯。**

### 1.2 评测系统的定位

| 维度 | Agent 本体 | 评测系统 |
|:---|:---|:---|
| 用户 | App 终端用户 | 研发 / PM |
| 输入 | 实时事件 + 用户消息 | 预设用例集 |
| 输出 | 对话回复 + 工具调用 | CSV 报告（30 列） |
| 运行时机 | 线上持续运行 | 每次变更后手动触发 |
| 可观测性 | 有限（线上日志） | 完整（trace + 规则检查 + 评分） |

### 1.3 设计理念

| 原则 | 说明 |
|:---|:---|
| **画像驱动** | 以完整用户画像（而非零散 prompt）组织用例，保证上下文完整性 |
| **分层评价** | 确定性检查秒出结论、硬性失败直接拦截，主观评价按需配置 |
| **每轮可审** | CSV 每行 = 一轮交互，多轮 case 展开为多行，tool call 链路完全可见 |
| **预留扩展** | 细粒度指标（per-turn token、per-step 耗时）和主观评分维度预留列位，无需改 schema |

---

## 二、用例体系

### 2.1 画像选择

4 个画像覆盖 Agent 面对的核心差异维度：

| 画像 | 人设 | 干预阶段 | 画像详细度 | 用例数 | 设计意图 |
|:---|:---|:---|:---|:---|:---|
| A | 夜猫子上班族，睡前手机 | 干预中期 | 丰富 | 15 | 测试中期干预闭环：建议→提醒→反馈→跟进 |
| B | 刚注册的新用户 | 零阶段 | 空/极少 | 10 | 测试冷启动：信息极少时不乱猜、多轮渐进收集 |
| C | 大学生，作息混乱 | 首次干预 | 中等 | 12 | 测试首次干预：不急于给方案、尊重用户节奏 |
| D | 作息规律但近期变差 | 长期用户 | 丰富 | 12 | 测试异常检测：识别偏离并温和询问原因 |

**选择原则**：画像之间在睡眠问题类型、干预阶段、画像详细度、生活场景上差异最大化。

### 2.2 用例结构

每个用例（case）定义一次完整的 Agent 调用输入及其预期行为：

```
{
  "id": "A04",
  "name": "用户主动求建议·完整干预闭环",
  "event_context": {
    "event_type": "user_message",       ← 触发类型
    "timestamp": "2026-03-25T21:00:00+08:00"
  },
  "scene_instruction": "...",           ← 可选：注入 system prompt 的场景上下文
  "messages": [                         ← 对话消息（支持多轮）
    {"role": "user", "content": "我想改善一下睡眠，有什么建议吗？"}
  ],
  "expected_tool_calls": "get_strategy([...]) → set_reminder → ...",
  "expected_response": "应该给一条具体建议，不用列表格式..."
}
```

### 2.3 事件类型覆盖

| 事件类型 | 触发方式 | 典型 case |
|:---|:---|:---|
| `user_message` | 用户发送消息 | A01 吐槽加班、A04 求建议、B03 多轮对话 |
| `app_open` | 用户打开 App（无消息） | A06 新数据推送、B07 首夜数据 |
| `feedback_submit` | 用户提交反馈卡 | A08 做到了、A09 没做到 |
| `push_click` | 用户点击推送消息 | A10 放手机提醒 |

### 2.4 多轮对话用例

部分 case 的 `messages` 包含多轮 user/assistant 交替消息，测试 Agent 在上下文累积下的表现：

| Case | 轮数 | 测试意图 |
|:---|:---|:---|
| B03 | 3 轮 | 新用户多轮对话，逐步了解后才给初步方向 |
| C11 | 2 轮 | 有课前一晚，主动给轻推 |

多轮 case 在 CSV 中按轮次展开为多行（`turn_index` 1, 2, 3...），case 级评价只在最后一行填充。

---

## 三、评测流水线

### 3.1 整体流程

```
profile-*.json + user-contexts/*.yaml
         │
         ▼
    ① run_eval.py
       组装 system prompt（身份 + 用户速览 + 样式 + 场景指令）
       + 工具定义 + messages
       → 调用 Agent API → 收集 trace
         │
         ├─→ traces/{run_id}_{case_id}.json
         │
         ├─→ ② 确定性检查（毫秒级，零成本）
         │
         ├─→ ③ 效率指标统计
         │
         ├─→ ④ 主观评价（可选）
         │
         ▼
    reports/{run_id}.json
         │
         ▼
    ⑤ generate_full_csv.py
       关联 profile + user-context + trace + report + rules
       → 生成 30 列 CSV
         │
         ▼
    reports/{run_id}_full.csv
```

### 3.2 第 ① 步：运行 Agent

对每个 case，按照 Agent 设计文档的 4 层 system prompt 拼接规则组装请求：

| System Prompt 层 | 内容来源 |
|:---|:---|
| 身份与核心原则 | Agent 设计文档（固定） |
| 用户速览 | `user-contexts/profile-{x}.yaml` 的 `[summary]` 段 |
| 输出样式 | Agent 设计文档（固定） |
| 场景指令 | case 的 `scene_instruction` 字段 |

运行后保存完整 trace：tool_calls 序列、response_text、token_usage、agent_loop_rounds。

### 3.3 第 ② 步：确定性检查

基于 `graders/rules.json` 做零成本、毫秒级的规则检查：

| 规则类型 | 作用域 | 示例 |
|:---|:---|:---|
| `blacklist_phrases` | 全局 | "系统检测到"、"根据数据分析" 等 8 个禁止短语 |
| `no_markdown_formatting` | 全局 | 禁止 `#`标题、`**`加粗、`-`列表、`1.`编号 |
| `tool_calls_required` | case | A04 必须调 `get_strategy` |
| `tool_calls_forbidden` | case | A01 禁止调 `get_health_data` |
| `response_blacklist` | case | A01 禁止出现"睡眠建议"、"早点睡" |
| `response_blacklist_refs` | case | A04 引用共享词组 `redline_coffee` |
| `response_max_sentences` | case | A01 回复不超过 3 句 |
| `response_must_not_be_list` | case | A04 回复不能用列表格式 |

**严重级别**：
- `hard_fail`：硬性失败，跳过后续评价，直接标记不合格
- `soft_fail`（默认）：记录但不阻断
- `severity_override`：case 级别覆盖默认严重级别（如 A12、D07 将特定规则升级为 hard_fail）

### 3.4 第 ③ 步：效率指标

从 trace 中提取资源消耗指标：

| 指标 | 说明 | 异常判断 |
|:---|:---|:---|
| `tool_call_count` | 工具调用总次数 | 单轮超过 6 次标记 soft_fail |
| `agent_loop_rounds` | Agent 内部循环轮数 | 超过 3 轮标记 soft_fail |
| `token_usage` | 总 token 消耗 | 单次超过 2000 标记 soft_fail |

### 3.5 第 ④ 步：主观评价（PM 自定义）

不预设固定评分维度。PM 可按需编写 judge prompt，定义：
- 评分维度（如任务完成度、语气自然度、共情程度等）
- 每个维度的权重和评分标准
- 输出格式（分数 + 评语 + 结构化 JSON）

judge 输出写入 CSV 的 `subjective_score`、`subjective_note`、`subjective_raw` 三列。

**当前状态**：预留为空，待 PM 配置 judge prompt 后启用。

### 3.6 第 ⑤ 步：生成完整 CSV

`generate_full_csv.py` 关联 5 类数据源，输出 30 列 CSV：

| 数据源 | 提供的信息 |
|:---|:---|
| `profile-*.json` | case 定义、预期行为（expected_tool_calls / expected_response） |
| `user-contexts/*.yaml` | 用户速览（注入 system prompt 的 summary） |
| `traces/*.json` | 实际 tool_calls、response_text |
| `reports/{run_id}.json` | 确定性检查结果、效率指标 |
| `graders/rules.json` | 规则定义（用于生成 rules_applied 摘要） |

---

## 四、CSV 报告规格

### 4.1 基本结构

- **每行 = 一轮 user-agent 交互**
- 单轮 case：1 行；多轮 case：N 行（N = 用户消息数）
- **30 列，分 4 组**
- 编码：UTF-8 with BOM（Excel 兼容）

### 4.2 列定义

#### 第 1 组：输入 (10 列)

| # | 列名 | 粒度 | 说明 |
|:---|:---|:---|:---|
| 1 | `profile_id` | case | 画像 ID（A / B / C / D） |
| 2 | `profile_name` | case | 画像名 |
| 3 | `case_id` | case | 用例 ID |
| 4 | `case_name` | case | 用例名 |
| 5 | `turn_index` | turn | 当前轮次（从 1 开始） |
| 6 | `event_type` | case | 触发类型 |
| 7 | `event_timestamp` | case | 事件时间 |
| 8 | `user_context_summary` | case | 用户速览 |
| 9 | `scene_instruction` | case | 场景指令 |
| 10 | `user_message` | turn | 该轮用户消息 |

#### 第 2 组：过程 (7 列)

| # | 列名 | 粒度 | 说明 |
|:---|:---|:---|:---|
| 11 | `agent_loop_rounds` | turn | Agent 循环轮数 |
| 12 | `tool_call_count` | turn | 工具调用次数 |
| 13 | `tool_calls_detail` | turn | 工具调用链（箭头格式） |
| 14 | `turn_input_tokens` | turn | *预留* — 该轮输入 token |
| 15 | `turn_output_tokens` | turn | *预留* — 该轮输出 token |
| 16 | `turn_duration_ms` | turn | *预留* — 该轮耗时 |
| 17 | `per_step_durations` | turn | *预留* — 各步骤耗时 |

#### 第 3 组：输出 (1 列)

| # | 列名 | 粒度 | 说明 |
|:---|:---|:---|:---|
| 18 | `response_text` | turn | Agent 实际回复全文 |

#### 第 4 组：评价 (12 列)

case 级别，多轮 case 中只在最后一行填充。

**4a. Guideline（用例预期）**

| # | 列名 | 说明 |
|:---|:---|:---|
| 19 | `expected_tool_calls` | 预期工具调用 |
| 20 | `expected_response` | 预期回复行为 |
| 21 | `rules_applied` | 适用规则摘要 |

**4b. Guideline 满足情况**

| # | 列名 | 说明 |
|:---|:---|:---|
| 22 | `det_pass_rate` | 确定性检查通过率 |
| 23 | `det_all_passed` | 是否全部通过 |
| 24 | `det_hard_fail` | 是否硬性失败 |
| 25 | `det_failed_checks` | 失败项详情 |
| 26 | `total_token_usage` | 总 token |
| 27 | `total_duration_ms` | *预留* — 总耗时 |

**4c. 主观评价（PM 自定义）**

| # | 列名 | 说明 |
|:---|:---|:---|
| 28 | `subjective_score` | PM 定义的评分 |
| 29 | `subjective_note` | PM 定义的评语 |
| 30 | `subjective_raw` | judge 返回的完整 JSON |

### 4.3 列值格式

**`tool_calls_detail`** — 紧凑箭头链：
```
get_strategy({"aspects":["action"]}) → set_reminder({...}) → suggest_replies({...})
```

**`rules_applied`** — 全局 + case 规则摘要：
```
全局:blacklist(8词)+no_markdown(4式) | case:tool_required(get_strategy)+must_not_be_list
```

**`per_step_durations`**（预留）— 步骤耗时链：
```
get_strategy:120ms → model_inference:450ms → suggest_replies:80ms
```

---

## 五、迭代流程

```
发现问题 → 加回归 case → 加规则（如适用） → 修复 prompt/工具 → 跑 eval → 对比 CSV
```

| 步骤 | 操作 | 产出 |
|:---|:---|:---|
| 发现问题 | 手动使用中发现 Agent 回复不对 | 问题描述 |
| 加回归 case | 把触发问题的输入加到对应画像的 cases | profile JSON 更新 |
| 加规则 | 如果问题可用关键词/工具判断，在 rules.json 新增 | rules.json 更新 |
| 修复 | 修改 system prompt 或工具定义 | Agent 代码更新 |
| 跑 eval | `python run_eval.py` | trace + JSON 报告 |
| 生成 CSV | `python generate_full_csv.py` | 完整 CSV |
| 对比 | 新旧 CSV 逐 case 对比 pass_rate、token、失败项 | 回归分析 |

---

## 六、用法

```bash
# 运行评测
python run_eval.py                         # 全部画像
python run_eval.py --profile A             # 只跑画像 A
python run_eval.py --case A01 A12 D07      # 只跑指定 case
python run_eval.py --deterministic-only    # 只跑确定性检查（零成本快速验证）

# 生成完整 CSV
python generate_full_csv.py                # 使用最新 report
python generate_full_csv.py --run-id 20260410_143200
```

---

## 七、文件清单

| 文件 | 用途 |
|:---|:---|
| `eval/profile-{a,b,c,d}-*.json` | 4 个画像定义（共 49 case） |
| `eval/user-contexts/profile-{a,b,c,d}.yaml` | 用户上下文（注入 system prompt） |
| `eval/graders/rules.json` | 确定性规则（全局 + 18 条 case 专属） |
| `eval/graders/deterministic.py` | 确定性检查器 |
| `eval/run_eval.py` | 评测主入口 |
| `eval/generate_full_csv.py` | 完整 CSV 生成脚本 |
| `eval/traces/{run_id}_{case_id}.json` | Agent 运行 trace |
| `eval/reports/{run_id}.json` | 评测原始结果 |
| `eval/reports/{run_id}_full.csv` | 完整 CSV 报告 |
