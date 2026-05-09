---
name: prd-prototype
description: 根据 PRD 生成 app 产品原型 HTML。基于根目录 prototype-template.html 复制 + 按屏改写。仅在 PRD 已锁定后用，需求讨论阶段不要触发。
---

# prd-prototype

把 PRD 落成可点可改的高保真原型 HTML。**先列屏，再画**——不直接出成品；不批量生成；一屏停一次。

## 触发

- 用户明确说"出原型 / 画原型 / 生成 html / 出高保真"
- prd-creator 写完一份 PRD 后委托
- 用户要在已有原型上加屏 / 改屏

需求讨论 / PRD 还没定稿阶段不要用。

## 模板基线

**所有原型必须基于** `prototype-template.html`（根目录）。这套模板提供四件能力，禁止重写：

1. **直接编辑**：所有 `__edit` class 的元素都可点击编辑文本与字号
2. **覆盖保存**：File System Access API（Chrome 首次选文件授权 → 后续 Cmd/Ctrl+S 直接覆盖原文件）
3. **Tweaks 控件**：右下浮动面板，自动收集 `[data-screen]` 屏列表，含模式切换 / 重放动效 / 标注显隐
4. **标注**：标注模式下点击组件创建 SVG 连线 + 文本框；一键显隐

不要替换或精简模板的脚本/CSS。只动 `<header>` 标题与 `.board` 内的 `.screen-wrap`。

## 视觉基线

iSho 已实现界面是**深色 + 圆角手机外框 + iOS 类卡片**。新原型必须延续：

- 手机外框：360×780，圆角 44px，深色岛屏
- 配色：背景 `#0a0a0c`，卡片 `#1c1c1e`，强调蓝 `#2e7df6`
- 字体：Noto Sans SC + Reddit Sans（已在模板里加载）
- 参考已有原型：`prd/sleep-debt-card/preview.html`、`prd/improve-tab/原型-v2.html`

不要发明新视觉语言；如 PRD 涉及全新组件，先用模板里已有的 `.scr-card / .scr-tabs / .scr-bars` 等同类组件改造，实在缺再加。

## 执行流程

### 步骤 1 · 读 PRD，列屏

读 PRD 主文档，把"会出现的屏"拆出来。每屏一行：

```
我从 PRD 拆了 N 屏：

屏 01 · <名字> · <这屏在做什么 · 来源页（从哪里进）>
屏 02 · <名字> · <一句话>
屏 03 · <名字> · <一句话>
...

打算放到：<原型路径>
按 屏 01 → 屏 02 → ... 顺序写，一屏停一次确认。

确认这个屏列表吗？或者哪里要拆/合？
```

**屏列表必须用户确认。** 改完了再进步骤 2。

简单需求只有 1-2 屏的，列表也要发，但简短："1 屏 · 主屏卡片，确认开写吗？"

### 步骤 2 · 拷贝模板

确认后，把 `prototype-template.html` 拷到 PRD 同目录，命名 `原型.html`（或用户指定）：

```bash
cp /Users/trendol/Documents/iSho/test/prototype-template.html <PRD-dir>/原型.html
```

如果同目录已有 `原型.html` / `prototype.html`，问用户是覆盖还是叠加版本号。

### 步骤 3 · 一屏一屏改

**每屏分批 Edit，不要一次写完所有屏。** 按 CLAUDE.md 的分批输出原则。

每屏要做的事：

1. 改 `<header>` 标题与副标题（仅第一次）
2. 替换 / 复制 `.screen-wrap` 块——保留外层结构，改内部组件
3. 给屏挂 `data-screen="屏 ID"` `data-screen-title="屏标题"`（tweaks 自动识别）
4. 给所有需要可编辑的文本加 `class="__edit"` —— **包括 PRD 里写出来的所有文案**
5. 屏标题 caption（`.screen-caption`）写清"屏号 · 标题 · 来源"

**写完 1 屏停下来：**「屏 01 完成（路径 X）。要继续屏 02，还是先调整这屏？」

用户说继续 → 写下一屏；说改 → 改完再问；说重来 → 退步骤 1。

### 步骤 4 · 收尾

所有屏写完后，告诉用户怎么用：

```
✅ 原型完成 · <路径>

打开方式：在 Chrome 里直接打开（双击或拖入）
- 浏览模式：默认，正常预览
- 编辑模式：点文本直接改，浮动工具条调字号
- 标注模式：点组件加注释，连线 + 文本框
- Cmd/Ctrl+S 保存：首次会让你选择本文件授权，之后直接覆盖

不支持原地覆盖的浏览器（Safari/Firefox）会下载新文件。
```

不调任何审查 skill。

## 写作铁律

- **零发明组件**：模板里能用的就用模板的，不另起样式块。需要新组件时尽量复用 `.scr-card / .scr-bars` 的 token（`--phone-elev / --phone-ink-60 / --r-card`）
- **所有可见文案都加 `__edit`**：用户最终会自己改文案，编辑模式才有用
- **每屏挂 data-screen + data-screen-title**：tweaks 面板自动收集，不挂就不出现在屏导航
- **不写交互逻辑**：原型是静态画面，跳转用 tweaks 切屏；不要写 JS 把屏 1 跳到屏 2 这种
- **禁假数据膨胀**：示例数据 1-3 条够说明问题就停，不要堆"演示用"的列表
- **禁未在 PRD 出现的屏**：原型只画 PRD 写过的屏。PRD 没的灰区先在屏列表里问用户加不加

## 常见组件速查（模板已有）

| 组件 | class | 用途 |
|---|---|---|
| 手机外框 | `.phone` | 360×780 深色机身 + island + home indicator |
| 状态栏 | `.status-bar` | 9:41 + 信号 |
| 屏标题 | `.scr-title` | 大标题（Tab 标题） |
| 卡片列表 | `.scr-list` > `.scr-card` | 主屏列表的卡片容器 |
| 卡片头 | `.scr-card-h` | 标题行 + 箭头 |
| 卡片大数 | `.scr-card-main` + `.scr-card-num/-unit` | 数据展示 |
| 详情头 | `.scr-detail-h` | 返回 + 标题 |
| 段落 Tab | `.scr-tabs` > `.scr-tab` | 日/周/月切换 |
| 大数 + 标签 | `.scr-big-num` | 详情页核心指标 |
| 横向条形对比 | `.scr-bars` > `.scr-bar-row` | 类似睡眠债的"需要 vs 实际" |
| 底部说明 | `.scr-note` | 灰色注释 |

PRD 里需要的组件不在表里 → 先看 `prd/sleep-debt-card/preview.html` 和 `prd/improve-tab/原型-v2.html` 是不是已经实现过；都没有再写新组件。

## 修改已有原型

- 直接 Edit 原文件，不留 changelog
- 加屏：在 `.board` 末尾插入新 `.screen-wrap`，挂 `data-screen`
- 删屏：直接删除该 `.screen-wrap`，连带它的标注（`[data-target]` 指向被删元素的）
- 改屏：定位到对应 `[data-screen="..."]` 改内部，不动其他屏

写完同样停下来问"继续吗"。
