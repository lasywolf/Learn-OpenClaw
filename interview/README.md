# interview/ · Agent 面试宝典

clone 本仓库即拥有一份可直接用的面试宝典：每章「简答 + 扩展分析 + 追问预测」，
观点型话术为主，所有判断对齐 Claude Code / Codex 的实际做法。

**一句话总纲**：agent 工程的收益不来自结构的精巧，来自轨迹对模型后训练分布的贴合。
所有「看起来更聪明」的设计，都要先回答一个问题：模型见过这个吗？

## 章节地图

| 章 | 文件 | 主题 |
|---|---|---|
| 01 | [01-agent-loop.md](./01-agent-loop.md) | agent 循环、自研轻框架、goal 长任务、工具做减法 |
| 02 | [02-tool-mcp-skill.md](./02-tool-mcp-skill.md) | Tool/MCP/Skill 统一视角、function call 原理 |
| 03 | [03-rag-不推荐.md](./03-rag-不推荐.md) | RAG≈VectorDB、agentic retrieval、选型 |
| 04 | [04-memory-context.md](./04-memory-context.md) | 压缩触发、tool_calls 边界、KV cache、MEMORY.md |
| 05 | [05-复杂memory-不推荐.md](./05-复杂memory-不推荐.md) | MemGPT/mem0/Zep/A-MEM 机制介绍 + 批判 |
| 06 | [06-压缩-从prompt技巧到模型能力.md](./06-压缩-从prompt技巧到模型能力.md) | compaction 是 checkpoint、白马二、1M 窗口论 |
| 07 | [07-multi-agent.md](./07-multi-agent.md) | A2A 批判、subagent=上下文隔离、agent teams |
| 08 | [08-eval-sandbox-harness.md](./08-eval-sandbox-harness.md) | eval 分层、sandbox 信任边界、harness |
| 09 | [09-eval-量化指标.md](./09-eval-量化指标.md) | 完成率/token/耗时指标、定义完成、任务集建设 |
| 10 | [10-pi-mono-architecture-未验证.md](./10-pi-mono-architecture-未验证.md) | pi-mono 四模块拆解 + 架构图（未经实机验证） |

主题分组：基础（01–02）→ 检索（03）→ context 工程三连（04–06）→ 多智能体（07）→ eval（08–09）→ 项目架构（10）。
