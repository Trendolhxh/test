---
name: prd-workflow
description: |
  分轮次和用户协作生成一份 PRD（产品需求文档）。当用户要求"写 PRD"、"做需求文档"、"新功能需求"、"产品需求文档"、"feature spec"、"PRD 草稿"、"产品设计稿"、"需求评审稿"、"小改一下"、"加个埋点"、"调整文案"，或描述了一个待实现的产品功能/改动并希望进入 spec 阶段时触发。
  本 skill 强制先做 Mode Picker，再按所选模式（patch / standard / full）跑相应轮次，遵守"双读原则"（人读中文摘要 + 机器读结构化字段），每轮 advance condition 显式确认。
license: Internal
---

# PRD Workflow Skill

把"AI 一次写完 8000 字 PRD，人读不动"的流程切成**模式 + 轮次**。先选模式（决定走完整 8 轮、缩减 5 轮、还是单文件 1 轮），再按 advance condition 渐进推进。

## Core principles（必须遵守）

1. **先选模式**：进入任何轮次前，**必须先做 Mode Picker**。
2. **小批次**：AC 一次 ≤ 7 条，决策一次 ≤ 5 个，候选问题一次 ≤ 8 个。
3. **双读**：人读中文（叙事 + 表格的"结论列"），机器读英文 ID/字段名。**禁止把长中文（>30 字）塞进 yaml 字段值**——长内容归独立 md 文件。
4. **决策点显式化**：`[DECISION-NEEDED id=DEC-XX]` 标签，未消解禁止进入实现。
5. **状态机**：`drafting → reviewing → frozen`。
6. **AI 主动暴露盲点**：每轮收尾追问"我可能漏了什么？给 3 个候选"。
7. **Round 5 必须开新会话**（仅 Full 模式强制；Standard 推荐；Patch 跳过）。
8. **禁止一次性写完整份 PRD**。
9. **prd.md 必须叙事化**：§1 必须有 ≥150 字中文叙事段；§2 决议表必须含"决议"列（一句话结论）；§3 AC 概览必须 2–3 句叙述；§4 必须有屏幕清单表。**禁止把章节做成纯链接索引。**
10. **PRD 和 ADR 只写最终结论，不写取舍过程**。Round 2 的 options/pros/cons 只在对话内出现，不落任何文件。

## Metric 政策

**Metric 不是必需流程项**。是否设 metric 由产品判断：

- **建议设置**：增长功能、数据驱动改造、A/B 实验
- **可省略**：基础功能页面、UI 改造、合规修复、单纯能力补齐

若省略，需在 `status.yaml.deviations` 留痕（`{item: "metric", reason: "基础功能页面无独立指标"}`），并在 `prd.md` TL;DR 显式标注 `metrics: []  # 故意省略，见 deviations`。

AC 不强制关联 metric。**AC 必须关联 ≥1 个 DEC**；如真无相关 DEC，显式写 `related_decisions: []  # 独立 AC，无关联决策`。

## PM vs Engineering Boundary（强制）

PRD 只写**用户感知层**的事，不写**实现选型层**。冲突时 PM 写"用户期望/行为/边界"，研发写"实现方式"。

**PM 该给的（写进 PRD/AC/契约）**：

- 用户故事、入口/出口
- AC 行为（given/when/then）
- UI 形态、状态枚举、文案变体
- 用户看到的错误文案 + 触发场景 + 恢复方式
- 用户看到的数据：字段中文名、单位、显示规则
- 用户感知的性能："点击后 1 秒内出结果"、"用户无感电量变化"
- 数据新鲜度/离线的**用户预期**：是否离线可读、多久算"旧"、何时刷新（用户视角）
- 算法不确定态 → 用户看到什么
- 埋点事件语义（产品分析职责）
- non-goals + deviations

**PM 不该给的（实现选型，全部归研发）**：

- ❌ API 定义：路径、method、request/response schema、HTTP 状态码
- ❌ 错误码：英文 ID、错误码枚举、error code 命名
- ❌ 数据 schema：数据库表结构、ORM、字段类型定义
- ❌ 缓存/存储：存储介质、TTL 数字、缓存策略、local DB
- ❌ 刷新机制：observer / polling / WebSocket / push 选型
- ❌ UI 实现技术：slot-based / virtual scroll / lazy load
- ❌ 算法实现：模型架构、训练参数、内存/CPU 数字、I/O JSON Schema、采样率精确值
- ❌ 状态管理：Redux / Zustand / MobX / Provider
- ❌ 硬件实现：通信协议（BLE/WiFi/I2C）、传感器型号、uA/mA 数字

**判断标准**：如果一句话的主语是"系统/服务/组件"而不是"用户"，它大概率不该出现在 PRD 里。

**典型反例**（这些字眼出现在 PRD/AC/contracts 里就是越界，lint 会 warn 或 fail）：

- "POST /api/xxx"、"返回 200"、"response body 含"
- "error code: INVALID_INPUT"、"错误码枚举"
- "复用现有 X observer"、"复用 X middleware"
- "slot-based 方案"、"virtual scroll"、"lazy load"
- "local DB"、"本地缓存层"、"Redux"、"Zustand"
- 缓存 TTL 写死具体小时数（应给"容忍度"）
- "JSON Schema"、"request body"、"response schema"

---

## Mode Picker（每次最先做）

进入 Round 0 之前，AI 先做以下推断：

### 三个模式

| 模式 | 适用 | 产出 | 走哪些轮次 |
|---|---|---|---|
| **patch · 微调** | 改文案/颜色/默认值/小修复/加埋点；1 工种；0–1 决策点；1 天内 | 单文件 `patches/{slug}.md` | 跳 Round 0–6，仅做 Patch Card |
| **standard · 标准** | 复用现有组件，无新硬件/算法；2–3 工种；2–5 决策点；1–2 周 | 完整目录 + Round 3.5 表格化（不出 HTML） | Round 0/1/2/3/3.5(表格)/4/(5 同会话)/6 |
| **full · 完整** | 新屏幕/跨硬件/算法/多端；≥3 工种；≥5 决策点；≥2 周 | 完整目录 + 所有 HTML | 全 8 轮（含 1.5、3.5 出 HTML、Round 5 必须新会话） |

### AI 怎么决定模式

收到用户需求后**先用 1 段话评估**这 4 个维度（不要直接进 Round 0）：

```yaml
ui_impact: none | reuse_existing | new_screens
roles_involved: [pm, design, frontend, backend, algo, hardware, qa]
decision_points_estimate: 0-1 | 2-5 | >5
risk: low | medium | high   # 合规/付款/医疗/不可回滚 = high
```

**判定规则**：
- `ui_impact=none` 且 `roles_involved≤2` 且 `decisions≤1` 且 `risk=low` → patch
- `ui_impact=new_screens` 或 `decisions>5` 或 `algo|hardware ∈ roles` 或 `risk=high` → full
- 其他 → standard

输出格式：

> 我的评估：UI=reuse_existing，工种=[pm, frontend, backend]，决策≈3，风险=low → 建议 **standard 模式**。该模式跳 Round 1.5、Round 3.5 用表格代替 HTML、Round 5 同会话执行即可。是否进入？

**用户可以直接覆盖**（"用 patch 就好" / "升到 full"）。`status.yaml.mode` 固化所选模式。

### 模式升级（中途调档）

任意轮次发现复杂度超出当前模式时，AI 必须主动提议升级：
- patch → standard：发现需要决策点、跨工种、或要画 UI
- standard → full：决策点超 5、新增屏幕、引入算法/硬件

升级时：保留已有产物，补齐缺失的轮次和模板。`status.yaml.deviations` 记录"升级时点 + 原因"。

**禁止反向降级**（已经写过的不要扔）。

---

## 语言约束

| 区域 | 语言 |
|---|---|
| 文档标题、正文、TL;DR 字段值（**短**）、文案变体、AC 描述 | **中文** |
| 长中文（≥30 字的论述/背景/决议详情） | **写在独立 md 文件，yaml 字段只放一句话标签** |
| ID（REQ/AC/DEC/SCR/state） | **英文**（`AC-01`、`SCR-02.low_signal`） |
| YAML/JSON 字段名、文件名、目录名、代码标识符 | **英文** |
| Glossary | 中英对照 |

违反者 lint 失败。

---

## Setup（按模式不同）

### Patch 模式（最简）

```
patches/
└── {slug}.md            # 单文件，从 templates/patch.md 拷贝
```

不需要 `status.yaml`、不需要 adr/contracts/ui，直接进 PR。

### Standard / Full 模式

```
specs/{slug}/
├── prd.md                              # 主入口
├── status.yaml                         # 状态机 + mode
├── problem-card.md                     # Round 0
├── acceptance-criteria.yaml            # Round 3
├── adr/ADR-XX.md                       # Round 2，每决策一份
├── ui/                                 # 仅 full 模式：HTML；standard 模式：本目录可能为空
├── contracts/{data-expectations,events,algorithm-boundary}.yaml  # Round 4 产品契约
└── reviews/{self-review-*.md, signoff.md}          # Round 5/6
```

`prd.md` 顶部固定结构（**章节正文不能为空或纯链接，否则 lint 失败**）：

```markdown
---
feature: {slug}
mode: standard | full       # 由 Mode Picker 决定
version: v0.1
status: drafting
---

# {中文功能名}

# TL;DR
\`\`\`yaml
# 从 templates/tldr-card.md 拷贝
# 必含字段：intent, product_shape（形态锚点）, non_goals, user_value, risk
# 可选字段：metrics（省略时 deviations 留痕）, deviations
# decisions_made 只允许 [{id, tag}]，禁止塞长描述
\`\`\`

# 1. 背景与用户故事
{**强制中文叙事段，≥150 字 ≤500 字**。融合 problem-card 的三件事：
 - 用户痛点（含 2–3 条用户原话引用）
 - 这个页面承担什么角色
 - 与现有功能/历史的关系
**禁止只写"见 problem-card.md"。**}

# 2. 决策记录

| ID | 议题 | **决议** | 详情 |
|---|---|---|---|
| DEC-01 | 评价阈值 | 4 档（完美/良好/需注意/严重影响） | [ADR-01](adr/ADR-01.md) |
| DEC-02 | 睡眠行 | 默认展开 | [ADR-02](adr/ADR-02.md) |

**只写最终结论，禁止写取舍过程**（取舍归 ADR 内部，且 ADR 也只在"背景"段简述）。

# 3. AC 概览
{**2–3 句中文叙述**，例如："这页承诺 N 件事：核心是 A（AC-XX）+ B（AC-YY）；边界覆盖 C/D（AC-ZZ）；交互覆盖 E/F（AC-NN）。"}

完整列表见 [acceptance-criteria.yaml](acceptance-criteria.yaml)。

# 4. UI 屏幕清单

| SCR | 中文名 | 状态数 | 关键状态 | 关联 AC |
|---|---|---|---|---|
| SCR-01 | 日视图 | 7 | 正常/欠佳/无数据/骨架/缓存/缺失/降级 | AC-01,02,03,06,12,13 |

完整 UI 平铺：[screens.html](ui/screens.html)（full 模式）

# 5. 产品契约
- [数据期望](contracts/data-expectations.yaml)：用户看到的数据、错误文案、新鲜度、离线预期
- [埋点](contracts/events.yaml)：产品分析事件
- 算法边界：{不适用 / 见 [algorithm-boundary.yaml](contracts/algorithm-boundary.yaml)}
⚠️ 这里只写产品契约（用户感知层），技术设计归研发。

# 6. Glossary（中英对照）

| 中文 | 英文 ID | 说明 |
|---|---|---|

# 7. 审查与签字
- Round 5 自审：[reviews/](reviews/)
- Round 6 签字：[reviews/signoff.md](reviews/signoff.md)
```

`status.yaml` 最小内容：

```yaml
feature: {slug}
mode: standard              # patch | standard | full
state: drafting             # drafting | reviewing | frozen
current_round: 0
owners: {pm: '', design: '', frontend: '', backend: '', algo: '', qa: '', hardware: ''}
candidate_decisions: []
decisions: {}
deviations: []
frozen_at: ''
```

---

## 各模式工作流

### Patch 模式（仅 1 步）

收到需求 → AI 直接渲染 `templates/patch.md` → `patches/{slug}.md`：含 TL;DR (≤100 字)、Why、Change、≤3 条 AC、test_hint、影响范围。用户确认即完成。**不分轮次。**

如果中途发现需要决策、要画 UI、跨工种 → 升级到 standard。

### Standard / Full 模式：8 轮

每轮标注 `[Mode]` 表示是否参与/简化。

#### Round 0 · 问题对齐 ` [standard ✅ | full ✅]`

**做**：基于用户需求反问 5–8 个澄清问题（用户/场景/痛点/历史竞品/合规/已有能力）。渲染 `templates/problem-card.md` → `specs/{slug}/problem-card.md`。

**Advance**：所有字段非空，无"待定/TBD"，**所有 advance check checkbox 全部勾完**（包括"用户显式回复进入 Round 1"）。

#### Round 1 · 意图骨架 ` [standard ✅ | full ✅]`

**做**：渲染 `templates/tldr-card.md` 嵌入 `prd.md` 的 `# TL;DR` 段。
- `candidate_decisions` 由 AI 列出"会卡住的所有点"，**禁止自己拍板**
- `product_shape` **必填**——一句话形态锚点（"参考 X 的 Y 结构 / 在 App 哪个位置 / 类比 Z"），让评审 5 秒能脑补出形态
- `metrics` 可选；若省略须在 `deviations` 留痕
- `decisions_made` 仅允许 `[{id, tag}]`，禁止塞长描述

**同时写 §1 背景叙事**：≥150 字，融合 problem-card 的痛点/角色/历史。

**Advance**：TL;DR ≤ 200 中文字；`product_shape` 非空；`candidate_decisions` ∈ \[3, 8]；§1 ≥150 字；用户确认。

#### Round 1.5 · 概念草图 HTML ` [standard ⏭️ skip | full ✅ 按需]`

**仅 full 模式**，且仅对"光看文字拍不准"的 DEC（典型：UI 形态、信息架构、交互模式）。AI 主动建议给哪些 DEC 出草图，用户许可后执行。

**HTML 结构**（每 DEC 一份 `ui/round-1.5-{DEC-ID}.html`）：
- 单文件、自包含、无 CDN
- 顶部 banner ⚠️ throwaway 草图
- 多列并排 2–3 个候选：手机线框 + 优劣势 + 影响 + 推荐度
- 底部投票按钮
- **故意丑**：禁用 design token 和精修视觉

**Advance**：每份 HTML ≥ 2 候选；用户对每份选 A/B；写入 `status.yaml.pending_decisions`。

#### Round 2 · 决策澄清 ` [standard ✅ | full ✅]`

**做**：在**对话中**给每条 candidate 展示 question/options/pros&cons/impact/recommendation——这一段**只在对话里出现，不落任何文件**。用户拍板后：

1. 回填 `prd.md` §2 决议表（"决议"列写一句话结论）
2. 同时回填 TL;DR `decisions_made` 字段：`[{id: DEC-01, tag: "4 档评价"}]`（仅一句话 tag）
3. 写一份**极简 ADR**：`adr/ADR-XX.md`（用 `templates/adr.md`，只含决议；背景 ≤3 行；无辩论段）
4. 写入 `status.yaml.decisions`

**约束**：一次 ≤ 5 条决策。取舍过程**不进入任何持久化文件**。

**Advance**：所有 candidate 都有 ADR；`prd.md` §2 决议表的"决议"列全部非空（≥4 中文字）；用户确认。

#### Round 3 · AC 切片 ` [standard ✅ | full ✅]`

**做**：用 `templates/acceptance-criteria.yaml` 分批生成，**每批 ≤ 7 条按主题切**：happy_path / suppression / degradation / performance / edge / error。

**约束**：可量化、有 test_hint、**关联 ≥1 DEC**（metric 可选）、禁模糊词。如真无相关 DEC，显式写 `related_decisions: []  # 独立 AC`。

**Advance**：所有 DEC 至少被 1 条 AC 引用；总数 ≥ 6 且分布在 ≥ 2 个主题；**§3 AC 概览段已写**（2–3 句叙述）。

#### Round 3.5 · UI 规格 ` [standard 📋 表格 | full 🖼️ HTML]`

**Standard 模式**：在 `prd.md` 的"4. UI 规格"段直接嵌入屏幕表格：

```yaml
ui:
  - screen: SCR-01
    name_zh: 心率告警通知
    states:
      - id: default
        copy: "您的心率持续偏高..."
        related_ac: [AC-01]
      - id: dismissed
        related_ac: [AC-04]
```

如果 ≥3 屏 或 ≥3 状态/屏，提议升级到 full。

**Full 模式**：**一份 `ui/screens.html` 把所有 SCR × 所有 state 平铺**（不再每屏拆文件）。

HTML 结构：
- 单文件、自包含
- `:root` 绑 design tokens；样式区**禁止任何颜色字面量**（含 hex / rgba / hsl / named color 如 `red`/`blue`）；所有颜色必须 `var(--token)`
- 移动真机视口（iPhone 393×852 或表盘比例）
- **平铺布局**：横向多列或瀑布流，每列一个 SCR；列顶 caption 写 SCR-ID + 中文名 + 关联 AC；列内是该 SCR 所有 state 的 phone mockup 子卡片，每个子卡片标注：state 英文 ID + 中文名 + 关联 AC 标签 + 简要文案
- 顶部可选 SCR/state filter（不强制）
- 每个 state 区域有 `data-scr` `data-state` `data-ac` 属性，方便 lint 抓取

**约束**：每个 state 必须显式标 ≥ 1 条 AC；**prd.md §4 屏幕清单中的 SCR 列表必须与 HTML 中的 SCR 一致**；算法不确定态（low_confidence / timeout / model_unavailable）必须出现为显式 state。

**Advance**：每屏在 HTML 中已平铺；prd.md §4 表格填好；每条交互类 AC 至少被一个 state 覆盖。

#### Round 4 · 产品契约 ` [standard ✅ 缩减 | full ✅ 完整]`

**做**：从 AC 反推产品契约（**不是技术设计**），落到 `contracts/`：
- standard：通常只需 `data-expectations.yaml` + `events.yaml`
- full：加 `algorithm-boundary.yaml`；硬件需求写在 `data-expectations.yaml` 的 `hardware_needs` 段

⚠️ **只写用户感知层**：用户看到的数据/错误文案/刷新时机/离线预期/埋点/算法不确定态的 UI 映射。禁止写 API 路径、request/response schema、错误码 ID、数据库 schema、缓存 TTL 数字——这些归研发。

每块按 owner 签字。

**Advance**：每条 AC 至少能对应到一个 contract 字段；user_facing_errors 每条有用户文案；算法不确定态全部有 UI 映射；签字完成。

#### Round 5 · 自洽审查 ` [standard 同会话即可 | full 必须新会话]`

**做**：AI 输出 `templates/self-review.md` 的启动 prompt 给用户。

- standard：可同会话执行（用 prompt 让 AI 切角色挑刺即可）
- full：**必须新对话**，避免 self-reinforcing bias

输出 `reviews/self-review-{date}.md`。

**Advance**：每条问题 ✅接受/❌驳回/✏️改；接受的回到对应轮次修复并 bump 版本；清单清空。

#### Round 6 · 终审签字 ` [standard ✅ | full ✅]`

**做**：渲染各角色视图。各 owner 在 `templates/signoff.md` 自己段落打勾。全员签字后切 `frozen`，打 git tag。

**Advance**：所有非空 owners 已签字。

---

## Lint

`scripts/lint.py specs/{slug}/`（standard/full）或 `scripts/lint.py patches/{slug}.md`（patch）。

lint 自动从 `status.yaml.mode` 读模式调整规则：
- patch：只检查 patch.md 必填字段（TL;DR ≤100 中文字、≥1 条 AC、test_hint）
- standard：跳过 ui/ 目录检查，但检查 `prd.md` 含屏幕清单表
- full：完整规则（含 HTML 颜色字面量检查、算法不确定态↔UI 映射、prd.md 叙事化）

详见 `scripts/lint.py`。

---

## Anti-patterns（禁止）

- 跳过 Mode Picker 直接进 Round 0
- patch 模式被滥用做大需求
- AI 自己拍板 candidate_decisions
- 一次给用户 > 7 条 AC
- Full 模式 Round 5 在同会话执行
- frozen 后改不 bump 版本
- HTML 中用颜色字面量（含 hex / rgba / hsl / named）
- AC 不可量化
- 用户偏离流程时强行执行（应记录 deviation 并继续）
- **prd.md §1/§2/§3/§4 写成纯链接索引**
- **取舍过程写进 prd.md 或 ADR**（PRD 和 ADR 只看结论）
- **yaml 字段值塞长中文（>30 字）**——长内容应去独立文件
- **在 PRD/AC/contracts 中写 API 定义**（路径、method、schema、HTTP 状态码）
- **在 PRD/AC/contracts 中写错误码 ID**（英文 error code 归研发）
- **在 contracts 中写 OpenAPI / JSON Schema**（PM 只给用户看到的字段语义）
- **主语是"系统/服务/组件"的描述**出现在 PRD 中（PRD 主语应该是"用户"）

## 节奏礼仪

- 一开始用一句话评估并提议模式："建议 standard，是否进入？"
- 每轮开始："进入 Round X · {名称}（mode={mode}），目标 Y，预计 Z 个回合。"
- 每轮结束："Round X 完成。Advance：✅✅❌（说明哪条没过）。是否进入下一步？"

## Templates

| 文件 | 用在 |
|---|---|
| `templates/patch.md` | Patch 模式单文件 |
| `templates/problem-card.md` | Round 0 |
| `templates/tldr-card.md` | Round 1（嵌入 prd.md） |
| `templates/adr.md` | Round 2（**极简**，仅决议） |
| `templates/acceptance-criteria.yaml` | Round 3 |
| `templates/contracts.yaml` | Round 4 产品契约（data-expectations / events / algorithm-boundary） |
| `templates/self-review.md` | Round 5 启动 prompt + 骨架 |
| `templates/signoff.md` | Round 6 |

Round 1.5 / 3.5（仅 full）的 HTML 不预置模板，AI 按上文结构现场生成。`example/` 目录有可参考示例。
