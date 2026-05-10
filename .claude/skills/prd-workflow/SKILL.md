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
3. **双读**：人读中文，机器读英文 ID/字段名。
4. **决策点显式化**：`[DECISION-NEEDED id=DEC-XX]` 标签，未消解禁止进入实现。
5. **状态机**：`drafting → reviewing → frozen`。
6. **AI 主动暴露盲点**：每轮收尾追问"我可能漏了什么？给 3 个候选"。
7. **Round 5 必须开新会话**（仅 Full 模式强制；Standard 推荐；Patch 跳过）。
8. **禁止一次性写完整份 PRD**。

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
| 文档标题、正文、TL;DR 字段值、文案变体、AC 描述 | **中文** |
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
├── contracts/{api,events,algorithm,hardware}.yaml  # Round 4
└── reviews/{self-review-*.md, signoff.md}          # Round 5/6
```

`prd.md` 顶部固定结构：

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
# (从 templates/tldr-card.md 拷贝)
\`\`\`

# 1. 背景与用户故事
# 2. 决策记录（指向 adr/）
# 3. AC 索引（指向 acceptance-criteria.yaml）
# 4. UI 规格（standard: 表格嵌入；full: 指向 ui/）
# 5. 跨职能契约（指向 contracts/）
# 6. Glossary
# 7. 自洽审查与签字（指向 reviews/）
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

**Advance**：所有字段非空，无"待定/TBD"，用户确认。

#### Round 1 · 意图骨架 ` [standard ✅ | full ✅]`

**做**：渲染 `templates/tldr-card.md` 嵌入 `prd.md` 的 `# TL;DR` 段。`candidate_decisions` 由 AI 列出"会卡住的所有点"，**禁止自己拍板**。`metrics` 待 DEC 的留 `?`。

**Advance**：TL;DR ≤ 200 中文字；`candidate_decisions` ∈ \[3, 8]；用户确认。

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

**做**：每条 candidate decision 给标准化对比（question/options/pros&cons/impact/recommendation/needs_input_from）。用户拍板后回填 `prd.md` TL;DR、生成 `adr/ADR-XX.md`、写入 `status.yaml.decisions`。

**约束**：一次 ≤ 5 条决策。

**Advance**：所有 candidate 都有对应 ADR；`prd.md` 无 `?`；用户确认。

#### Round 3 · AC 切片 ` [standard ✅ | full ✅]`

**做**：用 `templates/acceptance-criteria.yaml` 分批生成，**每批 ≤ 7 条按主题切**：happy_path / suppression / degradation / performance / edge / error。

**约束**：可量化、有 test_hint、关联 ≥1 metric 或 DEC、禁模糊词。

**Advance**：所有 metric 至少被 1 条 AC 覆盖；所有 DEC 至少被 1 条引用；总数 ≥ 6 且分布在 ≥ 2 个主题。

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

**Full 模式**：每屏一份 `ui/round-3.5-{SCR-ID}.html`，**一次只发一份给用户 review**。

HTML 结构：
- 单文件、自包含
- `:root` 绑 design tokens；样式区外严禁 hex
- 移动真机视口（iPhone 393×852 / 表盘比例）
- 三栏：屏幕清单 / phone mockup + 状态 tabs / 注释面板（触发条件、关联 AC、文案变体、动效、异常处理、用到的 token）
- 全状态网格折叠面板

**约束**：每个 state 必须 ≥ 1 条 AC；算法不确定态（low_confidence / timeout / model_unavailable）必须有显式 UI 状态。

**Advance**：每屏 review 通过；每条交互类 AC 至少被一个 state 覆盖。

#### Round 4 · 契约对齐 ` [standard ✅ 缩减 | full ✅ 完整]`

**做**：从 AC 反推 `templates/contracts.yaml`，落到 `contracts/`：
- standard：通常只需 `api.yaml` + `events.yaml`
- full：四件齐全（含 `algorithm.yaml`、`hardware.yaml`）

每块按 owner 拆 ≤1 页 diff，签字。

**Advance**：每条 AC 至少映射 1 个 contract 字段；每块 owner 签字；错误码、失败语义已枚举。

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
- standard：跳过 ui/ 目录检查，但检查 `prd.md` 含屏幕表格段
- full：完整规则（含 HTML hex 检查、算法不确定态↔UI 映射）

---

## Anti-patterns（禁止）

- 跳过 Mode Picker 直接进 Round 0
- patch 模式被滥用做大需求
- AI 自己拍板 candidate_decisions
- 一次给用户 > 7 条 AC
- Full 模式 Round 5 在同会话执行
- frozen 后改不 bump 版本
- HTML 中用 hex 字面量
- AC 不可量化
- 用户偏离流程时强行执行（应记录 deviation 并继续）

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
| `templates/adr.md` | Round 2 |
| `templates/acceptance-criteria.yaml` | Round 3 |
| `templates/contracts.yaml` | Round 4（含 4 子段） |
| `templates/self-review.md` | Round 5 启动 prompt + 骨架 |
| `templates/signoff.md` | Round 6 |

Round 1.5 / 3.5（仅 full）的 HTML 不预置模板，AI 按上文结构现场生成。`example/` 目录有可参考示例。
