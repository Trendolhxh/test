---
name: prd-dev
description: 为某个模块撰写面向开发的 PRD。读 master PRD 和共享契约后，按模块在 modules/<name>/开发文档.md 的骨架里填入内容。目标全面完善（无长度上限），必含数据模型、状态机、接口契约、边界条件、异常处理、埋点。严禁写视觉美学判断和品牌叙事。强制分批，每次最多 1 个 H2 或 2 个 H3。
---

# prd-dev

为一个模块写**面向工程师**的 PRD。读者是前端 / 后端 / 客户端工程师，关注点是：数据怎么流、状态怎么转、接口长什么样、异常怎么处理、埋点怎么打。

## 何时触发

- prd-workflow 判定当前处于阶段 3 且用户要写 Dev PRD
- modules/<name>/开发文档.md 已有骨架

## 输入

模块目录路径。

## 输出

该目录下的 `开发文档.md`，按章节填实。

## 核心行为铁律

1. **写前必读**：
   - `../../主文档.md`（整份）
   - `../../shared/*.md`（骨架锚点引用的共享契约）
   - 本模块已写的 `界面设计.md`（如有）——UI 描述的状态/交互要能对应到 dev PRD 的状态机
2. **分批铁律**：单次 Write/Edit 最多 1 个 H2 或 2 个 H3。
3. **全面完善**：没有行数上限。工程师需要的细节都要写清楚。宁可详尽不可遗漏。但**不是啰嗦**——每句话要有工程决策价值。
4. **禁止写**：
   - 视觉美学判断（"让按钮看起来更友好"）
   - 品牌叙事 / 产品愿景（放在 master 里）
   - 未决策的"可能 A 也可能 B"——dev PRD 的每句话都要是已决策的
5. **引用优先于复制**：已经在 shared/ 里定义的数据结构，引用锚点即可，不要整段复制到本文件。
6. **所有 ID、字段名、状态名、事件名用英文**，不用中文。中文只用于说明。
7. **边界条件必须穷举**：每个外部输入（用户操作 / API 响应 / 定时器）都要列出 happy path 和至少 2 种异常路径。

## 章节骨架（固定）

```
# <模块名> · Dev PRD

> 锚点块

## 1. 定位与范围
## 2. 数据模型
## 3. 状态机
## 4. 交互流程（对齐 UI PRD）
## 5. 接口契约
## 6. 依赖关系
## 7. 边界条件与异常处理
## 8. 埋点
## 9. 性能 / 可观测性要求
## 10. 未决工程问题
```

按需开启，不适用的章节显式标注"不适用，因为 <理由>"。

## 每节写作指引

### §1 定位与范围

一句话回答：
- 这个模块在技术栈的哪一层（前端组件 / 后端服务 / 客户端 SDK？）
- 边界在哪（做什么 / 不做什么）
- 依赖哪些外部系统 / 其他模块

### §2 数据模型

所有本模块定义或消费的数据结构，用 TypeScript interface 或等价的伪代码列出：

```typescript
interface EventPin {
  id: string
  category: 'sleep' | 'workout'
  status: 'pending' | 'confirmed' | 'archived'
  anchor_id: string
  impact: -2 | -1 | 0 | 1 | 2  // 引用 shared/事件数据.md §impact
  // ...
}
```

**如果该结构已在 shared/ 定义**：不要复制，写 `见 shared/事件数据.md §EventPin`。

### §3 状态机

每个有状态的实体给一张状态转移表或图：

```
| from \ to | pending | confirmed | archived |
|---|---|---|---|
| (initial) | user_create | — | — |
| pending | — | user_confirm | user_discard |
| confirmed | — | — | auto_archive(+24h) |
```

每个转移注明触发条件（user_* / system_* / timer_*），以及转移时的副作用（发事件、写存储等）。

### §4 交互流程（对齐 UI PRD）

对 ui-prd §5 的每个交互关键帧，写工程侧的实现视角：

```
**用户点击主按钮**（对应 ui-prd §5）：
- 前置：<哪些状态才允许点击>
- 动作：调用 API `POST /v1/events`，payload = ...
- 成功：状态机转到 confirmed，发 event `event.confirmed`
- 失败：按 §7 的异常处理路径
- 耗时预算：≤ 200ms（含网络）
```

### §5 接口契约

本模块对外的 API / 事件 / 共享状态订阅：

```
**HTTP**：POST /v1/events
Request: { category, anchor_id, ... }
Response 200: { id, status: 'pending' }
Response 4xx: { error_code, message }

**事件**：emits `event.confirmed`, `event.archived`
Payload: { id, timestamp }

**订阅**：listens `user.idle` from core module
```

消费其他模块的接口也在此列出（反向）。

### §6 依赖关系

一张表列清所有依赖：

```
| 依赖对象 | 类型 | 失败时策略 |
|---|---|---|
| /v1/events API | 后端服务 | 重试 3 次后降级到本地缓存 |
| core.UserStore | 同进程模块 | 必需，无降级 |
| FontAsset | 静态资源 | 降级到系统字体 |
```

### §7 边界条件与异常处理

每个输入通道都要写：

```
**输入：API 响应**
- happy: 200 + 合法 payload → 正常流程
- 4xx: 记录错误码，UI 展示对应错误态（见 ui-prd §2 错误态）
- 5xx / timeout: 重试 3 次（退避 1s/2s/4s）后进入降级态
- 格式异常: 丢弃响应，记录 sentry，UI 保持上一次状态
```

**重要**：每个异常路径都要对应 UI PRD 里的某个状态。如果 UI PRD 没有对应状态 → **停下**，告诉用户 UI PRD 缺状态。

### §8 埋点

表格化：

```
| 事件名 | 触发时机 | 属性 | 用途 |
|---|---|---|---|
| hero.impression | 模块首次进入视口 | state, variant | 核心指标 L2 |
| hero.interact | 用户点击 | target, result | 漏斗分析 |
```

### §9 性能 / 可观测性

- 性能预算（首屏 / 交互耗时）
- 日志要求（关键路径必须 log 什么）
- 告警阈值（什么情况下要报警）

### §10 未决工程问题

```
- [ ] <问题描述> — 待决策人 / 决策依据 / deadline
```

不同于 pm-notes 的未决项（那是产品决策）——这里是**工程决策**（选型 / 架构 / 性能取舍）。

## 完成判据

- [ ] §2 §3 §5 §7 必填完整
- [ ] §4 与对应 ui-prd §5 一一对应，无遗漏
- [ ] 所有异常路径都有 UI 状态对应
- [ ] 引用共享契约而非复制
- [ ] 无视觉美学 / 品牌叙事内容
- [ ] 所有 ID、字段、状态、事件名用英文

满足后交还给 prd-workflow：
- 提醒用户可以调用 `prd-review`
- **agent 更新 `prd/<feature>/进度.md`**：该模块"开发文档"格子 ⏸→🟡；review 通过后 → ✅ + 追加变更日志一行
