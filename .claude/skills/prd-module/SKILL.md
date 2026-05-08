---
name: prd-module
description: 为复杂需求中的某一个模块写 `prd/<feature>/<模块>.md`（≤ 500 字）。同时往 feature 级 `原型.html` 里追加该模块的演示片段。遵守 prd-workflow 全局铁律。
---

# prd-module

## 骨架

```markdown
# <模块中文名>

> Status: Draft | Locked
> Base: 主文档.md

## 是什么 / 给谁解决什么
<1-3 句>

## 怎么解决
**流程**（mermaid · 业务语言）：
\`\`\`mermaid
flowchart LR
  ...
\`\`\`

**状态**：
- `状态 A`：一句话

**边界情况**：
- <情况> · 一句话处理

## 不做
- <被砍项> · 一句话理由
```

## 关键动作

1. **写前必读**：`主文档.md` 整份 + 同 feature 已写的其他模块 md（避免重复 / 看耦合）。
2. **md ≤ 500 字**（不含锚点块）。超即说明把 html 该承担的 UI 描述塞进 md 了——砍。
3. **不重复主文档**：引用即可。
4. **更新 feature 级 html**：md 落稿后回到 `prd/<feature>/原型.html`，把本模块的 UI 演示加进去（至少 2-3 种状态可见、关键交互可点击）。html 不写文字解释。
5. **完成后**：`Status: Locked` → 调 `prd-host`。
