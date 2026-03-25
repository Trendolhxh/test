# Claude Code 提示词调用逻辑架构图

> 基于 [Piebald-AI/claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts) v2.1.81 分析

## 一、总体架构流程图

```mermaid
flowchart TB
    subgraph INIT["🚀 会话初始化 (每次会话开始时一次性加载)"]
        direction TB
        A[用户启动 Claude Code] --> B[组装 System Prompt]
        B --> B1["System Section (156 tks)<br/>身份声明 + 输出格式"]
        B --> B2["Doing Tasks 模块 (共 ~700 tks)<br/>10 个子文件拼接"]
        B --> B3["Executing Actions with Care (590 tks)<br/>安全操作规则"]
        B --> B4["Tool Usage 模块 (共 ~600 tks)<br/>12 个子文件拼接"]
        B --> B5["Tone & Style (55 tks)<br/>简洁 + 代码引用格式"]
        B --> B6["Output Efficiency (177 tks)<br/>输出精简指令"]
        B --> B7["Fork Usage Guidelines (326 tks)<br/>子 agent 规则"]
        B --> B8["条件段: Auto Mode / Learning Mode / Git Status / Plan Mode"]

        B1 & B2 & B3 & B4 & B5 & B6 & B7 & B8 --> C[完整 System Prompt<br/>~2,300-3,600 tks]
    end

    subgraph TOOLS["🔧 工具定义 (随 System Prompt 一起加载, ~11,600 tks)"]
        direction TB
        T1["核心工具 (始终加载)"]
        T1 --> T1a["Read (440 tks) — 读文件"]
        T1 --> T1b["Edit (246 tks) — 编辑文件"]
        T1 --> T1c["Write (129 tks) — 写文件"]
        T1 --> T1d["Bash (全部子文件 ~1,200 tks) — 执行命令"]
        T1 --> T1e["Glob (122 tks) — 文件搜索"]
        T1 --> T1f["Grep (300 tks) — 内容搜索"]
        T1 --> T1g["Agent/Task (879+186 tks) — 子 agent 调度"]
        T1 --> T1h["TodoWrite (2,161 tks) — 任务管理"]
        T1 --> T1i["WebFetch (297 tks) — 网页抓取"]
        T1 --> T1j["WebSearch (321 tks) — 网页搜索"]
        T1 --> T1k["Skill (326 tks) — 技能调用"]
        T1 --> T1l["AskUserQuestion (287 tks)"]
        T1 --> T1m["NotebookEdit (121 tks)"]

        T2["高级工具 (条件加载)"]
        T2 --> T2a["ToolSearch — 按需发现延迟工具"]
        T2 --> T2b["EnterPlanMode (878 tks)"]
        T2 --> T2c["ExitPlanMode (417 tks)"]
        T2 --> T2d["Computer (161 tks) — Chrome 自动化"]
        T2 --> T2e["TeammateTool (1,645 tks) — Swarm"]
        T2 --> T2f["CronCreate (754 tks)"]
        T2 --> T2g["EnterWorktree / ExitWorktree"]
        T2 --> T2h["LSP (255 tks)"]
        T2 --> T2i["Sleep (154 tks)"]

        T3["MCP 工具 (用户配置的外部工具)"]
        T3 --> T3a["每个 MCP server 额外增加 1K-10K+ tks"]
    end

    subgraph MEMORY["📝 记忆文件 (随 System Prompt 注入, ~743 tks)"]
        M1["CLAUDE.md — 项目级指令"]
        M2["~/.claude/CLAUDE.md — 用户级指令"]
        M3["Session Memory — 会话记忆"]
    end

    C --> TOOLS
    TOOLS --> MEMORY
    MEMORY --> READY["✅ 就绪：等待用户输入"]

    style INIT fill:#1a1a2e,stroke:#e94560,color:#eee
    style TOOLS fill:#16213e,stroke:#0f3460,color:#eee
    style MEMORY fill:#1a1a2e,stroke:#e94560,color:#eee
```

## 二、运行时动态注入流程

```mermaid
flowchart TB
    USER[👤 用户发送消息] --> DISPATCH{消息类型判断}

    DISPATCH -->|普通对话| MAIN_LOOP
    DISPATCH -->|"/plan"| PLAN_MODE
    DISPATCH -->|"/review, /commit 等"| SKILL_INVOKE
    DISPATCH -->|"需要子 agent"| SUBAGENT_SPAWN

    subgraph MAIN_LOOP["主 Agent 循环"]
        direction TB
        ML1[分析用户意图] --> ML2{需要调用工具?}
        ML2 -->|是| ML3[选择工具 + 生成参数]
        ML3 --> ML4[执行工具]
        ML4 --> ML5{触发 Hook?}
        ML5 -->|是| ML6["注入 System Reminder<br/>(hook-success / hook-blocking-error)"]
        ML5 -->|否| ML7[返回工具结果]
        ML6 --> ML7
        ML7 --> ML8{任务完成?}
        ML8 -->|否| ML1
        ML8 -->|是| ML9[输出最终回复]
        ML2 -->|否| ML9
    end

    subgraph REMINDERS["⚡ System Reminders (运行时动态注入, 40+ 种)"]
        direction TB
        R1["文件状态变化"]
        R1a["file-modified-by-user-or-linter (97 tks)"]
        R1b["file-exists-but-empty (27 tks)"]
        R1c["file-truncated (74 tks)"]

        R2["Hook 执行结果"]
        R2a["hook-success (29 tks)"]
        R2b["hook-blocking-error (52 tks)"]
        R2c["hook-additional-context (35 tks)"]

        R3["模式切换"]
        R3a["plan-mode-is-active-5-phase (1,297 tks)"]
        R3b["exited-plan-mode (73 tks)"]

        R4["IDE 交互"]
        R4a["file-opened-in-ide (37 tks)"]
        R4b["lines-selected-in-ide (66 tks)"]

        R5["资源监控"]
        R5a["token-usage (39 tks)"]
        R5b["todowrite-reminder (98 tks)"]
        R5c["new-diagnostics-detected (35 tks)"]
    end

    ML4 -.->|事件触发| REMINDERS
    REMINDERS -.->|注入到上下文| ML1

    style MAIN_LOOP fill:#0f3460,stroke:#e94560,color:#eee
    style REMINDERS fill:#533483,stroke:#e94560,color:#eee
```

## 三、子 Agent 调度流程

```mermaid
flowchart TB
    MAIN["🤖 主 Agent<br/>(完整 System Prompt + 所有工具)"] -->|"Agent(subagent_type='Explore')"| EXPLORE
    MAIN -->|"Agent(subagent_type='Plan')"| PLAN
    MAIN -->|"Agent(subagent_type='general-purpose')"| WORKER
    MAIN -->|"Agent(subagent_type='claude-code-guide')"| GUIDE
    MAIN -->|"自定义 Agent"| CUSTOM

    subgraph EXPLORE["🔍 Explore 子 Agent"]
        direction TB
        E_SYS["Explore Prompt (517 tks)<br/>+ Explore 强项指南 (185 tks)"]
        E_TOOLS["可用工具: Read, Glob, Grep,<br/>WebFetch, WebSearch, Bash<br/>❌ 禁止: Edit, Write, Agent"]
        E_RULE["严格只读模式<br/>禁止创建/修改文件"]
        E_SYS --> E_TOOLS --> E_RULE
    end

    subgraph PLAN["📋 Plan 子 Agent"]
        direction TB
        P_SYS["Plan Mode Enhanced (680 tks)<br/>+ 5-Phase Planning (1,297 tks)"]
        P_TOOLS["可用工具: Read, Glob, Grep,<br/>WebFetch, WebSearch, Bash<br/>❌ 禁止: Edit, Write, Agent"]
        P_FLOW["5 阶段流程:<br/>1. 理解需求<br/>2. 深度探索代码<br/>3. 起草方案<br/>4. 验证方案<br/>5. 交付最终计划"]
        P_SYS --> P_TOOLS --> P_FLOW
    end

    subgraph WORKER["⚙️ Worker 子 Agent (通用)"]
        direction TB
        W_SYS["Worker Instructions (272 tks)<br/>+ Worker Fork Execution (370 tks)"]
        W_TOOLS["可用工具: 全部工具<br/>(但不再生成子 agent)"]
        W_RULE["直接执行指令<br/>返回结构化结果"]
        W_SYS --> W_TOOLS --> W_RULE
    end

    subgraph GUIDE["📖 Claude Guide Agent"]
        direction TB
        G_SYS["Claude Guide Agent (744 tks)"]
        G_TOOLS["可用工具: Glob, Grep, Read,<br/>WebFetch, WebSearch"]
        G_DATA["按需加载数据模板:<br/>API Reference (多语言)<br/>Agent SDK Patterns<br/>Tool Use Reference"]
        G_SYS --> G_TOOLS --> G_DATA
    end

    subgraph CUSTOM["🛠️ 自定义 Agent"]
        direction TB
        C_SYS["Agent Creation Architect (1,110 tks)<br/>定义自定义 agent 规范"]
        C_TOOLS["工具集由创建者指定"]
        C_SYS --> C_TOOLS
    end

    EXPLORE -->|"返回搜索摘要"| MAIN
    PLAN -->|"返回实施计划"| MAIN
    WORKER -->|"返回执行结果"| MAIN
    GUIDE -->|"返回 API/SDK 指导"| MAIN
    CUSTOM -->|"返回自定义结果"| MAIN

    NOTE["💡 关键机制:<br/>每个子 agent 拥有独立上下文窗口<br/>完成后只返回摘要给主 agent<br/>不会膨胀主 agent 的上下文"]

    style MAIN fill:#e94560,stroke:#fff,color:#fff
    style EXPLORE fill:#0f3460,stroke:#e94560,color:#eee
    style PLAN fill:#0f3460,stroke:#e94560,color:#eee
    style WORKER fill:#0f3460,stroke:#e94560,color:#eee
    style GUIDE fill:#16213e,stroke:#0f3460,color:#eee
    style CUSTOM fill:#16213e,stroke:#0f3460,color:#eee
    style NOTE fill:#533483,stroke:#e94560,color:#eee
```

## 四、上下文窗口管理流程

```mermaid
flowchart TB
    CTX["200K 上下文窗口"] --> ALLOC

    subgraph ALLOC["Token 分配"]
        direction LR
        A1["System Prompt<br/>~3,200 tks (1.6%)"]
        A2["Tool Definitions<br/>~11,600 tks (5.8%)"]
        A3["Memory Files<br/>~743 tks (0.4%)"]
        A4["MCP Tools<br/>0-55K tks (变量)"]
        A5["对话消息<br/>剩余空间"]
    end

    ALLOC --> GROWTH["对话持续增长..."]
    GROWTH --> CHECK{接近上下文上限?}

    CHECK -->|否| CONTINUE[继续对话]
    CHECK -->|是| COMPACT

    subgraph COMPACT["🗜️ 上下文压缩策略"]
        direction TB
        C1["服务端压缩 (主要策略)"]
        C1 --> C1a["Conversation Summarization (956 tks)<br/>压缩早期对话为摘要"]
        C1 --> C1b["Analysis Instructions (3种变体):<br/>Full (182 tks) / Minimal (157 tks) / Recent (178 tks)"]
        C1 --> C1c["Recent Message Summarization (559 tks)<br/>保留最近消息，压缩旧消息"]

        C2["工具结果清理"]
        C2 --> C2a["清除已处理的工具返回结果"]
        C2 --> C2b["清除 thinking blocks"]

        C3["子 agent 隔离"]
        C3 --> C3a["复杂任务委托给子 agent"]
        C3 --> C3b["子 agent 独立上下文"]
        C3 --> C3c["只返回摘要给主 agent"]

        C4["Tool Search 延迟加载"]
        C4 --> C4a["不预加载所有工具定义"]
        C4 --> C4b["按需发现，节省 85% token"]
    end

    COMPACT --> CONTINUE

    style CTX fill:#e94560,stroke:#fff,color:#fff
    style COMPACT fill:#0f3460,stroke:#e94560,color:#eee
```

## 五、Skill / Slash Command 调用流程

```mermaid
flowchart LR
    USER["用户输入 /commit"] --> SKILL_TOOL["Skill Tool (326 tks)<br/>匹配已注册 skill"]

    SKILL_TOOL --> EXPAND["展开为完整 Prompt"]

    EXPAND --> S1["/commit → Quick git commit (510 tks)"]
    EXPAND --> S2["/review → /review slash command (238 tks)"]
    EXPAND --> S3["/security-review → Security review (2,607 tks)"]
    EXPAND --> S4["/batch → Batch command (1,106 tks)"]
    EXPAND --> S5["/schedule → Schedule command (2,468 tks)"]
    EXPAND --> S6["/pr-comments → PR comments (402 tks)"]

    S1 & S2 & S3 & S4 & S5 & S6 --> EXEC["注入到主 agent 上下文<br/>作为系统指令执行"]

    style USER fill:#e94560,stroke:#fff,color:#fff
    style SKILL_TOOL fill:#0f3460,stroke:#e94560,color:#eee
    style EXEC fill:#533483,stroke:#e94560,color:#eee
```

## 六、数据模板按需加载（claude-code-guide agent 专用）

```mermaid
flowchart TB
    Q["用户问: 如何用 Claude API 做 tool use?"] --> GUIDE["claude-code-guide Agent"]

    GUIDE --> MATCH{匹配问题类型}

    MATCH -->|"API 用法"| API_REF
    MATCH -->|"Agent SDK"| SDK_REF
    MATCH -->|"Tool Use"| TOOL_REF

    subgraph API_REF["API Reference (按语言加载)"]
        direction TB
        AR1["Python (3,518 tks)"]
        AR2["TypeScript (2,837 tks)"]
        AR3["Go (4,341 tks)"]
        AR4["Java (4,770 tks)"]
        AR5["cURL (1,996 tks)"]
        AR6["C# (4,703 tks)"]
        AR7["PHP (2,381 tks)"]
        AR8["Ruby (696 tks)"]
    end

    subgraph SDK_REF["Agent SDK Patterns"]
        direction TB
        SR1["Python patterns (2,656 tks)"]
        SR2["TypeScript patterns (1,529 tks)"]
        SR3["Python reference (3,450 tks)"]
        SR4["TypeScript reference (3,209 tks)"]
    end

    subgraph TOOL_REF["Tool Use Reference"]
        direction TB
        TR1["Tool use concepts (3,939 tks)"]
        TR2["Python reference (5,106 tks)"]
        TR3["TypeScript reference (5,033 tks)"]
    end

    API_REF & SDK_REF & TOOL_REF --> ANSWER["生成回答返回给主 agent"]

    style GUIDE fill:#e94560,stroke:#fff,color:#fff
    style API_REF fill:#0f3460,stroke:#e94560,color:#eee
    style SDK_REF fill:#0f3460,stroke:#e94560,color:#eee
    style TOOL_REF fill:#0f3460,stroke:#e94560,color:#eee
```

## 七、安全审查流程

```mermaid
flowchart TB
    ACTION["Agent 要执行操作"] --> SEC_CHECK{安全检查}

    SEC_CHECK -->|"Bash 命令"| BASH_SEC
    SEC_CHECK -->|"自主模式操作"| AUTO_SEC
    SEC_CHECK -->|"读取可疑文件"| MALWARE_SEC

    subgraph BASH_SEC["Bash 安全层"]
        direction TB
        BS1["Sandbox 模式 (默认开启)"]
        BS1 --> BS2{"命令失败?"}
        BS2 -->|"sandbox 限制导致"| BS3["检查 5 类证据:<br/>access denied / network failure /<br/>operation not permitted /<br/>unix socket error / path restriction"]
        BS3 --> BS4["向用户解释限制<br/>请求 dangerouslyDisableSandbox"]
        BS2 -->|"其他原因"| BS5["正常错误处理"]
    end

    subgraph AUTO_SEC["自主模式安全监控"]
        direction TB
        AS1["Security Monitor Part 1 (2,726 tks)"]
        AS2["Security Monitor Part 2 (2,941 tks)"]
        AS1 --> AS3["评估操作风险等级"]
        AS2 --> AS3
        AS3 --> AS4{"高风险?"}
        AS4 -->|是| AS5["暂停并请求用户确认"]
        AS4 -->|否| AS6["继续执行"]
    end

    subgraph MALWARE_SEC["恶意软件分析"]
        direction TB
        MS1["Censoring Malicious Activities (98 tks)"]
        MS2["malware-analysis-after-read (87 tks)"]
        MS1 --> MS3["允许: 防御性安全、CTF、教育"]
        MS2 --> MS4["禁止: 增强恶意代码能力"]
    end

    style SEC_CHECK fill:#e94560,stroke:#fff,color:#fff
    style BASH_SEC fill:#0f3460,stroke:#e94560,color:#eee
    style AUTO_SEC fill:#533483,stroke:#e94560,color:#eee
    style MALWARE_SEC fill:#1a1a2e,stroke:#e94560,color:#eee
```

## 八、完整调用逻辑汇总

```mermaid
flowchart TD
    START["会话开始"] --> SP["1. 组装 System Prompt (~3.2K tks)"]

    SP --> SP1["System Section (身份)"]
    SP --> SP2["Doing Tasks × 10 (行为规则)"]
    SP --> SP3["Executing Actions with Care (安全)"]
    SP --> SP4["Tool Usage × 12 (工具优先级)"]
    SP --> SP5["Tone & Style (输出风格)"]
    SP --> SP6["Output Efficiency (精简)"]
    SP --> SP7["Fork Usage Guidelines (子agent规则)"]
    SP --> SP8["条件段: Auto/Learning/Git/Plan Mode"]

    SP --> TOOLS["2. 加载工具定义 (~11.6K tks)"]
    TOOLS --> T1["18 个内置工具\nRead/Edit/Write/Bash/Glob/Grep/Agent/Todo..."]
    TOOLS --> T2["ToolSearch (延迟加载其他工具)"]
    TOOLS --> T3["MCP 工具 (用户配置, 0-55K tks)"]

    TOOLS --> MEM["3. 注入记忆文件 (~743 tks)"]
    MEM --> M1["CLAUDE.md (项目级)"]
    MEM --> M2["~/.claude/CLAUDE.md (用户级)"]
    MEM --> M3["Session Memory"]

    MEM --> LOOP["4. 主 Agent 循环"]
    LOOP --> L1["接收用户消息"]
    L1 --> L2["动态注入 System Reminders\n← 文件变化/Hook/IDE/诊断/token 用量"]
    L2 --> L3["分析意图 → 选择工具 → 执行 → 观察结果"]
    L3 --> L4{"需要子 agent?"}
    L4 -->|"深度搜索"| L4a["Explore 子 agent (独立上下文)"]
    L4 -->|"规划"| L4b["Plan 子 agent (5阶段流程)"]
    L4 -->|"并行执行"| L4c["Worker 子 agent"]
    L4 -->|"API/SDK 问题"| L4d["claude-code-guide (按需加载数据模板)"]
    L3 --> L5{"/slash 命令?"}
    L5 -->|"是"| L5a["Skill Tool 展开并执行"]
    L3 --> L6{"上下文快满?"}
    L6 -->|"是"| L6a["触发压缩 (摘要化早期对话)"]
    L3 --> L7{"任务完成?"}
    L7 -->|"否"| L1
    L7 -->|"是"| END["会话结束"]

    END --> E1["Session Memory 更新"]
    END --> E2["Dream Memory Consolidation\n(706 tks, 如果启用)"]
```

---

## 关键设计启示（对构建类 Manus 产品的参考）

1. **模块化拼接 > 单体 Prompt**：66+ 个小文件按需拼接，而非一个巨大提示词
2. **工具定义即文档**：每个工具的 description 是给模型看的使用手册
3. **子 agent 隔离上下文**：复杂任务不膨胀主上下文，只返回摘要
4. **延迟加载**：ToolSearch 按需发现工具，数据模板按需加载
5. **动态注入 System Reminders**：40+ 种运行时事件通知，让模型感知环境变化
6. **分层安全**：Sandbox + Security Monitor + 用户确认，三层防护
7. **上下文预算意识**：System Prompt 只占 1.6%，为对话留足空间
