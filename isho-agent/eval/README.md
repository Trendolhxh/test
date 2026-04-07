# 评测系统

## 设计思路

以**用户画像**为核心组织单位。每个画像文件是一个完整的评测集，包含：
1. 用户画像（user_profile）
2. 干预策略（intervention_plan）
3. 评测用例列表：每个用例 = 事件上下文 + 场景指令 + 对话消息 + **预期回复描述**

## 画像选择原则

画像之间在以下维度上差异最大化：
- 睡眠问题类型（入睡困难 vs 时长不足 vs 质量差 vs 作息混乱）
- 干预阶段（新用户/首次干预/干预中期/长期用户）
- 画像详细程度（空画像 → 基础画像 → 丰富画像）
- 生活场景（上班族/学生/自由职业/宝妈）

## 评测流水线（三层架构）

```
eval/profile-*.json
        ↓
  批量脚本组装 API 请求（system prompt + tools + messages）
        ↓
  调用 agent，收集完整 trace（tool_calls + response + token_usage）
        ↓ 保存到 traces/
  ┌─────────────────────────────────────────────────────┐
  │ 第 1 层: 确定性检查（秒级）                           │
  │   规则文件: graders/rules.json                       │
  │   检查器:   graders/deterministic.py                 │
  │   内容: 红线关键词、禁止/必须工具调用、格式、句数上限    │
  │   输出: 每条规则 pass/fail + severity                │
  │   ⚡ 硬性失败 → 跳过后续层，直接标记失败               │
  └─────────────────────────────────────────────────────┘
        ↓ 通过
  ┌─────────────────────────────────────────────────────┐
  │ 第 2 层: 效率指标（秒级）                             │
  │   内容: tool call 次数、重复调用检测、agent loop 轮数   │
  │   输出: 效率 metrics，异常时标记 soft_fail            │
  └─────────────────────────────────────────────────────┘
        ↓
  ┌─────────────────────────────────────────────────────┐
  │ 第 3 层: LLM Judge 多维度评分（分钟级）                │
  │   评分器: graders/llm_judge.py                       │
  │   维度: Outcome(50%) / Process(20%) / Style(30%)    │
  │   输出: 结构化 JSON（每个维度 pass + score + note）    │
  └─────────────────────────────────────────────────────┘
        ↓
  生成报告 → reports/{run_id}.md + reports/{run_id}.json
```

### 为什么分三层？

| | 确定性检查 | 效率指标 | LLM Judge |
|--|-----------|---------|-----------|
| 速度 | 毫秒 | 毫秒 | 秒~分钟 |
| 成本 | 0 | 0 | API 调用费 |
| 可解释性 | 完全确定 | 完全确定 | 主观但结构化 |
| 适用范围 | 硬性约束（红线、格式） | 资源消耗 | 语气、共情、内容质量 |

原则：**快的先跑，确定性的先跑，硬性失败直接停**。LLM Judge 只负责人类才能判断的主观质量。

## 评分维度说明

### Outcome（任务目标，权重 50%）
回复内容是否满足 expected_response 中描述的行为？
- 是否回答了用户的问题
- 是否正确关联了干预方案
- 是否避免了不该做的事（如给新用户强行建议）

### Process（过程正确性，权重 20%）
工具调用是否合理？
- 是否调了该调的工具
- 是否避免了不该调的工具
- 参数是否正确（如 get_strategy 的 aspects 选择）

### Style（风格，权重 30%）
是否像朋友聊天而非 AI 报告？
- 语气自然、简短、有温度
- 不暴露系统机制（"系统检测到"）
- 不用 markdown 格式
- 不说教、不鸡汤

## 目录结构

```
eval/
├── README.md                           # 本文件
├── run_eval.py                         # 评测主入口
├── profile-a-night-owl.json            # 画像 A 评测集
├── profile-b-new-user.json             # 画像 B 评测集
├── profile-c-student.json              # 画像 C 评测集
├── profile-d-good-sleeper.json         # 画像 D 评测集
├── user-contexts/                      # 用户上下文 YAML
│   ├── profile-a.yaml
│   ├── profile-b.yaml
│   ├── profile-c.yaml
│   └── profile-d.yaml
├── graders/                            # 评分器
│   ├── __init__.py
│   ├── rules.json                      # 确定性规则配置
│   ├── deterministic.py                # 确定性检查器
│   └── llm_judge.py                    # LLM Judge（结构化评分）
├── traces/                             # 运行 trace 存档（git ignored）
│   └── {run_id}_{case_id}.json
├── reports/                            # 评测报告
│   └── {run_id}.md / {run_id}.json
└── memory-v3-tools.md                  # 记忆架构 v3 设计文档
```

## 画像列表

| 文件 | 画像类型 | 干预阶段 | 画像详细度 | 用例数 |
|------|---------|---------|-----------|-------|
| profile-a-night-owl.json | 夜猫子上班族，睡前手机 | 干预中期 | 丰富 | 15 |
| profile-b-new-user.json | 刚注册的新用户 | 零阶段 | 空/极少 | 10 |
| profile-c-student.json | 大学生，作息极度混乱 | 首次干预 | 中等 | 12 |
| profile-d-good-sleeper.json | 作息规律但近期睡眠变差 | 长期用户 | 丰富 | 12 |

## 用法

```bash
# 运行所有画像
python run_eval.py

# 只运行画像 A
python run_eval.py --profile A

# 只运行指定 case
python run_eval.py --case A01 A12 D07

# 只跑确定性检查（快速验证，不花 LLM 钱）
python run_eval.py --deterministic-only
```

## 迭代流程

1. **发现问题**: 手动使用中发现 agent 回复不对
2. **加回归 case**: 把触发问题的输入加到对应画像的 cases 里
3. **加确定性规则**: 如果问题可以用关键词/工具调用判断，在 `rules.json` 中新增规则
4. **修复 prompt/工具**: 修改 system prompt 或工具定义
5. **跑 eval**: 确认修复生效 + 没有引入回归
6. **对比报告**: 新旧报告的趋势追踪表确认整体分数没降
