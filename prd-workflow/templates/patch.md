<!--
Patch Card · Mode A · 单文件需求/改动卡
位置：patches/{slug}.md
适用：改文案/颜色/默认值/小修复/加埋点；1 工种；0–1 决策；1 天内能做完
不需要 status.yaml、不需要 adr/contracts/ui，直接进 PR
中途发现复杂度超出（要画 UI / 跨工种 / 决策点 >1）→ 升级到 standard 模式
-->

---
slug: {{kebab-case-slug}}
mode: patch
created_at: {{ISO-8601}}
owner: {{name}}
---

# {{中文标题}}

## TL;DR
{{≤100 中文字。一句话讲清"改什么 + 为什么"}}

## Why
{{背景。如果是 design system 升级、合规要求、用户反馈，给出来源链接}}

## Change
{{具体改动。代码层级即可，例如：
- `Button.tsx`：默认 `borderRadius` 由 4 改为 8
- `tokens.json`：新增 `radius.button = 8`
}}

## Acceptance Criteria（≤ 3 条）
- AC-01: {{中文。可量化，禁止"差不多/较合理"}}
- AC-02: {{...}}

## Test hint
{{给 QA / Agent 写测试的提示，例如"视觉回归 + 现有单测不退化"}}

## Affects
- 影响 SCR：{{若涉及现有屏幕，列出 SCR ID}}
- 影响 token / API / event：{{...}}
- 不影响：{{显式列出未触及的部分，避免 review 时反复问}}

## Sign-off
- [ ] {{owner}} 签字
- [ ] PR 已挂 AC ID

---

**升级触发条件**：如出现以下任一情况，停止 patch 流程，转 standard：
- 需要 ≥ 2 个决策点
- 跨 ≥ 2 个工种
- 需要新增 UI 屏幕（不是改现有）
- 涉及合规、付款、医疗、不可回滚的操作
