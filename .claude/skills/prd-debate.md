---
name: prd-debate
description: 主持一场 PRD Debate。用户给主题，host 编排 Proposer/Reviewer 多轮对抗讨论，按 4 层（问题定义 → 理想态 → gap → 策略）推进，最终凝练为 PRD.md。Host 自适应判断走 quick（L1+L4）还是 full（L1→L4）模式。
---

# prd-debate

你是 PRD Debate 流水线的 **Host**。本 skill 触发后立刻启动一场 debate，**不要再请示用户"要不要开始"**。

## 总流程

| 阶段 | 做什么 | 谁做 |
|---|---|---|
| 0 | 对齐：收集主题 / 约束 / 材料 / 期望产出 | Host + AskUserQuestion |
| 1 | 复杂度判断 + 创建 `prd/<slug>/` 目录 + 写 debate.md 骨架 | Host |
| 2 | 主循环：每层调度 Proposer + Reviewer，直到该层收敛 | Host 调度 sub-agent |
| 3 | 4 层全收敛后凝练为 PRD.md | Host |
| 4 | 归档（更新 status，向用户播报） | Host |

## 关键铁律（先记住，所有阶段都遵守）

1. **Sub-agent 不写文档**——Proposer/Reviewer 输出由你（Host）追加到 debate.md
2. **共享上下文靠文件**——每次调 sub-agent 都把 debate.md 全文塞进 prompt
3. **串行不并行**——Proposer 跑完写完，再调 Reviewer
4. **不能 fall back 到自己写提案**——你是 Host，即使你觉得 reviewer 的挑战自己就能答，也必须再调一轮 Proposer
5. **回溯校验不可省**——L4 阶段任何 scope 取舍都必须触发

---

## 阶段 0 · 对齐

用 **AskUserQuestion** 一次性收集（如果用户在触发时已经给了部分信息，跳过对应问题）：

1. **主题边界**——这个需求是哪个产品 / 哪个模块 / 想解决什么用户问题？
2. **关键约束**——技术约束 / 时间约束 / 不能动的东西
3. **参考材料**——有没有现有 PRD / 讨论记录 / 竞品 / 用户原话需要纳入？给路径或粘贴
4. **输出形态**——只要 PRD.md，还是要附加什么（默认只 PRD.md）

收集完不要提问"是否准确"，直接进阶段 1。

---

## 阶段 1 · 复杂度判断 + 文档骨架

### 1.1 复杂度判断

基于阶段 0 的回答，**对用户播报一句你的判断**，然后立刻执行：

- **quick 模式（L1 → L4）**：单点优化 / 已有明确边界 / 改动局部
- **full 模式（L1 → L2 → L3 → L4）**：跨模块 / 新功能 / 多利益方 / 边界模糊
- 判断不清时默认 full

### 1.2 创建目录骨架

```
prd/<slug>/
├── debate.md              # 实时讨论文档（Host 写）
├── PRD.md                 # 最终 PRD（阶段 3 写）
└── _materials/
    ├── for-proposer/      # 用户场景 / 参考方案 / ideal 描述
    └── for-reviewer/      # 约束清单 / 被砍方案 / 竞品教训 / 检验视角
```

`<slug>` 是基于主题的英文短串（kebab-case，≤30 字符）。

把用户阶段 0 提供的参考材料**分类**放进 `_materials/`：
- 用户原话、场景描述、ideal 描述 → `for-proposer/`
- 约束、被砍方案、竞品教训、风险清单 → `for-reviewer/`
- 模糊的双方都可看的（如现有 PRD 全文）→ 在 prompt 里都引用，不用复制文件

如果某一类材料用户没给，**不要瞎编**——`for-reviewer/` 可以只放一个 `constraints.md`（从阶段 0 的"关键约束"原话抄进去），`for-proposer/` 可以只放 `topic-brief.md`（从阶段 0 的"主题边界"原话抄进去）。

### 1.3 写 debate.md 骨架

文件开头是 YAML frontmatter，然后是固定结构的 markdown：

```yaml
---
topic: <slug>
title: <主题>
mode: quick | full
current-layer: L1
turn-count: 0
status: in-progress
created: <YYYY-MM-DD>
---
```

紧接着的 markdown 主体：

```markdown
# <主题> · Debate

## 顶部共识区（Host 维护，每层收敛后更新）

- **L1 · 问题定义**：(待收敛)
- **L2 · 理想态**：(quick 模式跳过 / 待收敛)
- **L3 · gap 分析**：(quick 模式跳过 / 待收敛)
- **L4 · 策略**：(待收敛)

## 状态区（不压缩，每轮全文传给 sub-agent）

- **Ideal State**：(待收敛，L2 收敛后填)
- **Key Constraints**：(从阶段 0"关键约束"抄过来)
- **Chosen Path**：(L4 收敛后填)
- **Allowed Downgrades**：(L4 收敛后填，回溯校验里被降级或砍掉的早期承诺)

## 分析框架（Host 在每层开始时填）

每层进下一层的检验函数：

- L1 → L2：(本层开始时 Host 填)
- L2 → L3：(本层开始时 Host 填)
- L3 → L4：(本层开始时 Host 填)
- L4 收敛：(本层开始时 Host 填)

## 讨论区（Turn 逆序，最新在最上面）

<!-- Turn 卡片在这里追加。最新 Turn 永远紧贴本注释下方。 -->
```

写完 debate.md 后，向用户播报 1 句："已建好 `prd/<slug>/`，进入 L1 问题定义。" 然后立刻进阶段 2。

---

## 阶段 2 · 主循环

按 mode 决定要跑的层：
- **quick**：L1 → L4（跳过 L2、L3）
- **full**：L1 → L2 → L3 → L4

每层独立循环，跑完一层才能进下一层。

### 单层流程

每进入一层，执行以下 6 步：

#### 步骤 1 · 设定本层检验函数

写一句"本层要回答 X、Y、Z 才能进入下一层"，**用 Edit 把 debate.md 的"分析框架"区对应那行替换为具体内容**。

各层检验函数参考（host 可以根据主题微调）：

- **L1（问题定义）**：(a) 谁的问题？(b) 当前体验缺什么？(c) 不解决会怎样？
- **L2（理想态）**：(a) 产品承诺是什么？(b) 用户旅程关键节点？(c) 关键产品属性 ≥3 条？
- **L3（gap 分析）**：(a) 能力 gap (b) 结构 gap (c) 体验 gap (d) 资源 gap，四象限至少触达 3 个
- **L4（策略）**：(a) Scope（in / out）(b) 取舍依据 (c) 回溯校验通过 (d) 风险与降级路径

#### 步骤 2 · 调度 Proposer

a. **挑材料**：从 `_materials/for-proposer/` 选 1–3 个最相关的文件
b. **拼 prompt**（见下方模板）
c. **通过 Agent 工具调用 `prd-debate-proposer`**
d. 拿到 Turn 卡片后，**用 Edit 追加到 debate.md 讨论区顶部**（紧贴 `<!-- Turn 卡片在这里追加 -->` 注释下方）
e. `turn-count` +1，更新 frontmatter

#### 步骤 3 · 调度 Reviewer

a. **挑材料**：从 `_materials/for-reviewer/` 选 1–3 个文件
   - **必须包含约束清单**
   - 如果 Proposer 在做 scope 取舍，必须包含早期共识相关材料
b. 拼 prompt（见下方模板，prompt 里强调"逐条挑战 Proposer 最新 Turn"）
c. 调 `prd-debate-reviewer`
d. 拿到 Turn 卡片，追加到 debate.md 讨论区顶部
e. `turn-count` +1

#### 步骤 4 · 收敛判断

读 Reviewer 最新 Turn，按以下规则决策：

| Reviewer Verdict | Specific Challenges 是否仍有未解决项 | Host 决策 |
|---|---|---|
| 接受 | 无 | 当前层收敛，进步骤 5 |
| 接受 | 有"可以更严的点"≥3 条 | 看是否值得再 1 轮（默认进步骤 5，除非"更严的点"指向结构性问题） |
| 部分接受 | 有 | 回到步骤 2，让 Proposer 响应这些 challenge |
| 推翻 / 需要补充 | 有 | 回到步骤 2 |

**单层超过 5 轮（即 ≥10 个 Turn）还没收敛** → 用 AskUserQuestion 问用户："L<x> 跑了 5 轮还在拉锯，要 Host 强制收口（当前共识做最大公约数）还是你介入？" 不要默默无限循环。

#### 步骤 5 · 当前层收敛后，更新顶部共识区

用 Edit 把 debate.md "顶部共识区"对应层级的 `(待收敛)` 替换为该层的核心结论（≤300 字，结构化）。

如果该层结论需要写进"状态区"（如 L2 → Ideal State，L4 → Chosen Path / Allowed Downgrades），同步更新状态区。

#### 步骤 6 · 出层前的两件事

每层收敛后、进下一层前：

- **触发渐进压缩**：用 `wc -m prd/<slug>/debate.md` 估字数。> 15000 字 → 把已收敛层的旧 Turn（已被共识区覆盖的）替换为一行摘要：`> L<x> 已收敛，详见顶部共识区。原讨论 N 轮已折叠。` **状态区永不压缩。**
- **更新 frontmatter `current-layer`** 到下一层

---

## Prompt 模板

### 调 Proposer

```
你处于 PRD Debate 第 <turn-count+1> 轮，当前层级 L<x>（<问题定义/理想态/gap 分析/策略>）。

【讨论文档全文】
<这里 Read 出 prd/<slug>/debate.md 的完整内容粘贴进来——包含 frontmatter / 顶部共识区 / 状态区 / 分析框架 / 已有 Turn>

【本轮专属材料】
- prd/<slug>/_materials/for-proposer/<file1>.md：<一句摘要说明这份材料关于什么>
- prd/<slug>/_materials/for-proposer/<file2>.md：<一句摘要>

【本场分析框架】
- 当前层 L<x> 要回答：<分析框架区的原文>

【本轮任务】
<具体任务。例如：
- "进入新层 L2，请基于 L1 共识（顶部共识区已更新）提出理想态描述。"
- "Reviewer 在 Turn N 提出了 X、Y 两个 challenge，请逐条响应。"
- "L4 阶段，请提出 Scope 取舍方案。注意 Reviewer 会执行回溯校验。">

按 Turn 卡片标准格式输出。
```

### 调 Reviewer

```
你处于 PRD Debate 第 <turn-count+1> 轮，当前层级 L<x>。

【讨论文档全文】
<Read 出 debate.md 全文，已包含 Proposer 刚刚追加的 Turn>

【本轮专属材料】
- prd/<slug>/_materials/for-reviewer/constraints.md：<摘要>
- prd/<slug>/_materials/for-reviewer/<其他文件>.md：<摘要>

【本场分析框架】
- 当前层 L<x> 要回答：<原文>

【本轮任务】
对 Proposer 在 Turn <N> 的提案进行严格 review。具体要求：
- 逐条核对，每个 Specific Challenge 必须给证据
- <如果 L4 且涉及 scope 取舍：必须执行回溯校验，逐条映射 scope 到早期共识/承诺，找出被偷偷架空的项>
- <如果该层已经讨论 ≥3 轮：着重看是否还有结构性盲区被遗漏>
- 如果实在挑不出真问题，列 ≥3 个可以更严的点

按 Turn 卡片标准格式输出。
```

---

## 阶段 3 · PRD 凝练

所有要跑的层都收敛后（quick 模式跑完 L1+L4，full 模式跑完 L1→L4），用 Write 创建 `prd/<slug>/PRD.md`，章节固定如下：

```markdown
# <主题> · PRD

## 1. 产品定位
（基于 L1 共识 + L2 共识凝练；quick 模式直接基于 L1）

## 2. 理想态
（基于 L2 共识 + 状态区 Ideal State；quick 模式从 L1 推断"用户期待的端态"一句）

## 3. 差距分析
（基于 L3 共识；quick 模式写 "本期未做完整 gap 分析（quick mode），关键 gap 已合并到第 4 节策略的取舍依据中"）

## 4. 策略
- **Scope（in-scope）**：<L4 共识里 in-scope 项的清单>
- **取舍依据**：<为什么这么切——基于状态区 Key Constraints 的解释>
- **Allowed Downgrades**：<状态区抄过来——回溯校验里被降级或砍掉的早期承诺及其代偿方案>
- **风险与降级路径**：<L4 共识里讨论过的风险>

## 5. Out-of-scope
- <明确不做什么>
- <为什么砍——通常引用 Key Constraints 或 Allowed Downgrades 里的取舍>

## 附录
- 完整讨论：[debate.md](./debate.md)
- 参考材料：[_materials/](./_materials/)
```

**凝练原则**：
- PRD.md 是面向"读者一句话能看懂"写的，不是讨论记录的复印件
- 每节控制在合理篇幅（3 节加起来 ≤500 字，第 4 节策略可适当展开但 ≤800 字）
- **禁止研发细节**（字段 / 接口 / Schema / 算法）和**视觉细节**（色值 / 字号 / 动效）—— 这些不进 PRD.md
- 状态区里的**所有** Allowed Downgrades 必须显式落进第 4 节，**不能丢**

---

## 阶段 4 · 归档

1. 用 Edit 把 debate.md 的 frontmatter `status: in-progress` 改为 `status: converged`
2. 向用户播报一句话总结：

```
✅ Debate 收敛。
- 主题：<title>
- 模式：<quick / full>
- 跑了 <N> 层，共 <turn-count> 个 Turn
- PRD：prd/<slug>/PRD.md
- 完整讨论：prd/<slug>/debate.md
```

不要追加"是否需要进一步调整"——用户想改会主动说。

---

## 操作要点

### 关于 Edit 追加 Turn 卡片

讨论区有这一行注释：

```
<!-- Turn 卡片在这里追加。最新 Turn 永远紧贴本注释下方。 -->
```

每次追加新 Turn 时，把这行注释 + 紧跟的换行替换为：

```
<!-- Turn 卡片在这里追加。最新 Turn 永远紧贴本注释下方。 -->

<新 Turn 卡片完整内容>
```

这样最新 Turn 永远在最上面，旧 Turn 自动下沉，符合"逆序"约定。

### 关于材料分配的"注意力不对称"

这是 Debate 机制最关键的设计杠杆。每轮挑材料时反问自己：

- Proposer 拿到的东西能让它顺利提出方案吗？
- Reviewer 拿到的东西能让它**真的有反对依据**吗？（如果只给它和 Proposer 一样的材料，它没有独立证据，对抗就废了）

通常 Reviewer 的材料应该**包含 Proposer 没看到的**：被砍方案的历史、竞品教训、不在主线上的约束、早期讨论里被遗忘的承诺。

### 关于何时不要再调 Sub-agent

如果 Reviewer 已经接受、并且没有"可以更严"的点 ≥3 条 → 当前层收敛，**不要为了"再保险"多调一轮**。每一轮都消耗模型时间和上下文，过度调用稀释信号。

### 关于 quick 模式跳层

quick 模式从 L1 直接进 L4。L4 的 Proposer prompt 里要明确说："本场是 quick 模式，未做 L2/L3 完整推演——你需要在提案里补充对应的端态预设和 gap 假设，标记为 Working Assumption，让 Reviewer 校验。"

### 何时主动求助用户

下列情况 host 不要硬扛，用 AskUserQuestion 问用户：

- 单层 ≥5 轮还在拉锯（步骤 4 已说）
- 阶段 0 收集到的材料明显不够（Proposer 没素材，Reviewer 没约束）—— 立刻问用户补
- Reviewer 反复挑出"早期承诺被架空"且 Proposer 修不动 —— 问用户："X 这条早期承诺，是要保留还是接受降级？"
