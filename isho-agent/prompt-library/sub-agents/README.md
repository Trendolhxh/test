# 子 Agent 使用指南

> 本目录包含所有子 agent 的提示词模板和通用规则

## 架构概述

主 agent（精力管家）在对话中直接与用户交互。子 agent 在后台异步执行，不直接面对用户。

```
用户 ↔ 主 Agent（精力管家）
              ↓ 触发
         子 Agent（后台运行）
              ↓ 输出
         主 Agent 消费结果
```

## 当前子 Agent 清单

| 子 Agent | 触发时机 | 输入 | 输出 |
|----------|----------|------|------|
| memory-distiller | 新记忆累积到阈值 / 定时 | 当前用户上下文文档 + 新记忆列表 + 健康数据摘要 | 更新后的用户上下文文档 |
| conversation-summarizer | 对话上下文接近 token 上限 | 完整对话历史 | 9 区块结构化摘要 |

## 通用规则（所有子 agent 务必遵守）

### 隔离原则
- 子 agent 只能看到传入的数据，禁止访问主对话上下文
- 子 agent 之间禁止直接通信——通过 orchestrator 中转
- 子 agent 不持有状态——每次调用都是无状态的

### 输出规范
- 子 agent 的输出禁止直接展示给用户
- 输出格式务必严格遵循各自模板定义的结构
- 输出中禁止包含对用户的称呼或对话语气——子 agent 不是在和用户说话

### 错误处理
- 子 agent 执行失败时，orchestrator 应静默降级，禁止向用户暴露子 agent 的存在
- memory-distiller 失败 → 保留原文档不更新，新记忆保留在队列中等下次
- conversation-summarizer 失败 → 保留原始对话历史，不压缩

### Token 预算
- memory-distiller：输入 ~2000tk，输出 ~1500tk
- conversation-summarizer：输入 = 完整对话历史，输出 ≤ 500tk

### 未来扩展预留
新增子 agent 时务必提供：
1. 触发条件说明
2. 输入/输出格式定义
3. 系统提示词模板
4. 错误降级策略
