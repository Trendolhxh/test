# 开源 Agent 框架调研报告

> 调研日期：2026-03-24
> 目标：为构建类 Manus 的 agent 产品提供框架选型参考

## 一、GitHub 高质量开源 Agent 框架

### 1. OpenClaw (210K+ Stars)
- **简介**：2026 年增长最快的开源项目，由 PSPDFKit 创始人 Peter Steinberger 创建
- **特点**：插件生态丰富（ClawHub 5,700+ skills），社区活跃
- **适用场景**：开发者工作流自动化、浏览器自动化、个人生产力管理
- **GitHub**：搜索 "OpenClaw" 即可找到

### 2. LangGraph (24.8K+ Stars)
- **简介**：LangChain 生态的 agent 框架，2025年10月发布 1.0 GA
- **特点**：图结构工作流建模，精细的状态管理，Uber/LinkedIn/Klarna 等生产级应用
- **适用场景**：复杂企业级 agent、需要精确控制流的场景
- **GitHub**：https://github.com/langchain-ai/langgraph

### 3. CrewAI (44.3K+ Stars)
- **简介**：角色扮演式多 agent 协作框架，独立于 LangChain
- **特点**：原型速度比 LangGraph 快约 40%，原生支持 MCP 和 A2A
- **适用场景**：快速原型验证、团队式 agent 协作、业务流程自动化
- **GitHub**：https://github.com/crewAIInc/crewAI

### 4. AutoGen / Microsoft Agent Framework (54.6K+ Stars)
- **简介**：微软开源，2025年10月与 Semantic Kernel 合并为统一框架
- **特点**：事件驱动架构，多 LLM 集成，结构化对话流
- **适用场景**：多 agent 对话、企业级集成
- **GitHub**：https://github.com/microsoft/autogen

### 5. OWL by CAMEL-AI (11.2K+ Stars) ⭐ 最接近 Manus
- **简介**：开源通用 AI agent，GAIA 基准测试开源第一名
- **特点**：完全开源无需邀请码，基于 CAMEL-AI 框架，5天获得 11.2K stars
- **适用场景**：通用型自主 agent，Manus 的最佳开源替代
- **GitHub**：https://github.com/camel-ai/owl

### 6. OpenManus (16K+ Stars)
- **简介**：MetaGPT 核心贡献者 3 小时构建的 Manus 开源复刻
- **特点**：MIT 协议，支持 Playwright 浏览器自动化，Conda 快速部署
- **适用场景**：浏览器自动化、复杂工作流编排
- **GitHub**：https://github.com/FoundationAgents/OpenManus

### 7. AgenticSeek — "完全本地化的 Manus"
- **简介**：完全自主的网页浏览 agent
- **特点**：完全本地运行，专注数据提取和表单填写
- **适用场景**：隐私敏感场景、本地部署需求

### 8. MetaGPT
- **简介**：模拟软件公司协作的多 agent 框架
- **特点**：从自然语言需求生成完整工作流（用户故事→API设计→文档）
- **适用场景**：从需求到代码的全流程自动化

### 9. n8n
- **简介**：开源工作流自动化平台，支持 400+ 集成
- **特点**：可视化无代码 + 自定义代码混合，原生 AI 能力
- **适用场景**：无代码/低代码工作流自动化

## 二、官方 Agent SDK

| SDK | 提供方 | 说明 |
|-----|--------|------|
| **Claude Agent SDK** | Anthropic | Claude Code 的底层引擎，v0.1.48 |
| **OpenAI Agents SDK** | OpenAI | v0.10.2，支持 100+ 非 OpenAI 模型 |
| **Google ADK** | Google | v1.26.0 |

## 三、必读构建指南

### Anthropic 官方（强烈推荐）
1. [Building Agents with the Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk)
2. [Equipping Agents for the Real World with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
3. [Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)

### 社区指南
4. [How to Build an AI Agent: Complete Guide 2026](https://www.the-ai-corner.com/p/how-to-build-ai-agent-guide-2026) — 8步构建框架+模型成本对比
5. [Definitive Guide to Agentic Frameworks 2026](https://softmaxdata.com/blog/definitive-guide-to-agentic-frameworks-in-2026-langgraph-crewai-ag2-openai-and-more/) — 框架完整对比
6. [2026 AI Agent Framework Decision Guide](https://dev.to/linou518/the-2026-ai-agent-framework-decision-guide-langgraph-vs-crewai-vs-pydantic-ai-b2h) — 选型决策
7. [LangGraph vs CrewAI vs OpenAI Agents SDK](https://particula.tech/blog/langgraph-vs-crewai-vs-openai-agents-sdk-2026) — 三大框架对比

## 四、选型建议

### 构建类 Manus 产品的推荐路径

| 阶段 | 推荐框架 | 原因 |
|------|----------|------|
| 快速验证 | CrewAI 或 OpenManus | 原型速度最快 |
| 生产部署 | LangGraph | 状态管理和控制流最成熟 |
| 最接近 Manus | OWL (CAMEL-AI) | 开源通用 agent 排名第一 |
| 完全本地化 | AgenticSeek | 无需云端依赖 |
| 最大灵活性 | Claude Agent SDK / OpenAI Agents SDK | 底层 SDK，完全自定义 |

### 常见迁移路径
**CrewAI（原型验证）→ LangGraph（生产部署）**

### 核心洞察
2026 年最成功的 agent 系统（OpenAI Codex、Claude Code、Manus）都收敛到了同一个认知：
> **更简单的基础设施 + 更好的上下文管理 > 复杂的工具链**

Claude Code 只用了 4 个核心工具。Manus 重构了 5 次框架，每次迭代都更简单、更好。

## 五、实战参考：完整提示词 & 工具定义 & 上下文组装

### 5.1 Manus 完整架构（泄露版）

Manus 的内部实现已被完整提取，是学习 agent 产品设计的最佳参考。

**核心文件结构：**

| 文件 | 作用 |
|------|------|
| `Prompt.txt` | 主系统提示词：角色定义、核心能力、行为规则 |
| `Modules.txt` | 模块说明：写作规则、浏览器规则、编码规则 |
| `AgentLoop.txt` | Agent 循环：分析事件→选工具→等执行→迭代→提交 |
| `tools.json` | 29 个工具的 JSON Schema 定义 |

**关键设计模式：**
- 规划与执行分离：Planner 生成编号伪代码步骤，用 `todo.md` 实时追踪
- 纯工具调用：响应必须使用 function calling，禁止纯文本回复
- 工具名不暴露给用户
- 输出风格：禁止纯列表/bullet points，要求段落式散文

**查看地址：**
- [Manus tools and prompts (Gist)](https://gist.github.com/jlia0/db0a9695b3ca7609c9b1a08dcbf872c9)
- [x1xhlol/system-prompts - Manus](https://github.com/x1xhlol/system-prompts-and-models-of-ai-tools/tree/main/Manus%20Agent%20Tools%20&%20Prompt)
- [Manus 架构深度分析 (Gist)](https://gist.github.com/renschni/4fbc70b31bad8dd57f3370239dccd58f)
- [Manus Unveiled (Medium)](https://medium.com/@joycebirkins/manus-unveiled-dive-into-internal-prompts-workflows-and-tool-configurations-6ee9a7e0e708)

### 5.2 Claude Code 完整系统提示词 & 18 个工具

从 npm 编译源码中直接提取，保证与实际运行一致。

**架构亮点：**
- 系统提示词仅 2,300-3,600 tokens（占 200K 上下文的 ~1.6%）
- 工具定义 ~11,600 tokens，每个工具定义是一个"小手册"
- 子 agent（Plan/Explore/Task）独立上下文窗口
- Tool Search Tool 按需发现工具，节省 85% token

**查看地址：**
- [Piebald-AI/claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts)
- [x1xhlol/system-prompts - Claude Code](https://github.com/x1xhlol/system-prompts-and-models-of-ai-tools/blob/main/Anthropic/Claude%20Code/Prompt.txt)
- [Inside Claude Code's System Prompt](https://www.claudecodecamp.com/p/inside-claude-code-s-system-prompt)

### 5.3 OpenManus 代码结构（可运行的 Manus 复刻）

```
OpenManus/
├── app/agent/
│   ├── manus.py          # 主 Agent，继承 PlanningAgent
│   ├── base.py           # ReActAgent 基类（Think→Act→Observe）
│   └── toolcall.py       # ToolCallAgent，工具调用逻辑
├── app/prompt/
│   └── manus.py          # 系统提示词模板
└── app/tool/
    ├── browser_use.py    # 浏览器工具（Playwright）
    ├── file_saver.py     # 文件操作工具
    └── python_execute.py # Python 执行工具
```

继承链：`ReActAgent → ToolCallAgent → PlanningAgent → Manus`

**查看地址：**
- [FoundationAgents/OpenManus](https://github.com/FoundationAgents/OpenManus)
- [OpenManus 代码解析](https://dev.to/foxgem/openmanus-an-autonomous-agent-platform-8nl)

### 5.4 OWL/CAMEL-AI 上下文组装

**核心流程：**
1. `construct_society()` 创建 `OwlRolePlaying` 环境
2. 为 UserAgent/AssistantAgent 生成角色系统消息
3. Inception Prompting：只需初始概念，对话自然演化
4. 子 agent 维护隔离上下文（WebAgent 浏览器历史独立于主 agent）

**关键源码：**
- [camel/societies/role_playing.py](https://github.com/camel-ai/camel/blob/master/camel/societies/role_playing.py)
- [camel-ai/owl](https://github.com/camel-ai/owl)

### 5.5 万能参考仓库

- [x1xhlol/system-prompts-and-models-of-ai-tools](https://github.com/x1xhlol/system-prompts-and-models-of-ai-tools)（132K Stars）— Cursor、Devin、Lovable、Windsurf、Replit、v0、Perplexity 等所有主流 AI 产品的完整提示词和工具定义
- [dontriskit/awesome-ai-system-prompts](https://github.com/dontriskit/awesome-ai-system-prompts) — 分类整理的提示词集合
- [jujumilk3/leaked-system-prompts](https://github.com/jujumilk3/leaked-system-prompts) — 泄露提示词存档

### 5.6 构建类 Manus 产品需要关注的 4 个层面

| 层面 | 学什么 | 参考项目 |
|------|--------|----------|
| 系统提示词 | 角色定义、行为约束、输出风格 | Manus Prompt.txt, Claude Code Prompt |
| 工具定义 | JSON Schema 参数、使用场景描述 | Manus tools.json, Claude Code 18 tools |
| 上下文组装 | 状态管理、多轮记忆、子 agent 隔离 | OWL/CAMEL RolePlaying, Claude Code subagents |
| Agent 循环 | ReAct、规划-执行分离、todo 清单 | OpenManus agent/, Manus AgentLoop.txt |

## 六、市场数据

- 全球 agent 市场 2025 年达 78.4 亿美元，预计 2030 年达 526.2 亿美元（CAGR 46.3%）
- Gartner 预测 2026 年底 40% 企业应用将集成 AI agent（2025 年不到 5%）
- 57% 组织已在生产环境运行 AI agent（LangChain 调研数据）
