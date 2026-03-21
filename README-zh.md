# 这个tutorial能干什么
零基础一天 （9小时）学完agent！写这个教程就是想告诉大家，Agent其实非常简单！
并且能帮助你找到 Agent相关工作/实习！目前有很多个同学看我的教程找到了实习，且本教程在同学群里备受好评，现在开源给大伙！

## 总体内容展示

### 学会 Agent（学习需约 1天 * 9小时）

1. 拥有你自己的llm api-key（阅读需约15分钟）
   - 你可能需要学会使用python和[uv](https://docs.astral.sh/uv/getting-started/installation/) 用 rust 编写，类似于 rust 里面的 cargo，非常非常快
   - 为什么不用conda而是uv:uv 开源无商用风险，Conda 在超过 200 人的组织有[潜在商用授权问题](https://www.anaconda.com/blog/is-conda-free)
   - uv 可以像 pip 一样编辑镜像源，mac 和 linux 系统修改 `~/.config/uv/uv.toml` 并写入类似于下面的内容，Windows 系统可以自己查下怎么配置。项目初始化需要`uv sync`。
   ```
   [[index]]
   url = "https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple"
   default = true
   ```
   - 你可能需要llm api-key，推荐[kimi](https://platform.moonshot.cn/docs/overview)或者[智谱](https://open.bigmodel.cn)
   - 配置环境变量`OPENAI_API_KEY`和`OPENAI_BASE_URL`，并且尝试运行[`core/llm.py`](./core/llm.py)

2. 实现 Node / Workflow / Agent （阅读需约1小时）
   - 我们最终的目标是造一个Agent，能够联网搜索、运行命令行、文件编辑。
   - Agent底层可以使用Node来抽象，我已经准备好了一个极简的实现，可以看[`core/node.py`](./core/node.py)，不到60行就实现了一个Agent的轻框架，实在是太容易理解了！如果没有py基础看不懂，可以把代码复制给ai让它来解释。
   - 但我们应该怎么去用Node呢，我们可以新建3个Node并把它们串起来实现功能`接收输入->上网搜索->大模型生成总结`，恭喜你已经实现了workflow，相关实现已经在[`examples/workflow`](./examples/workflow)
   - 现在新建个workflow，实现功能`接收用户输入->大模型回复`，并且loop反复调用这个workflow，恭喜你已经实现了chatbot，相关实现已经在[`examples/chatbot`](./examples/chatbot)
   - 现在尝试给chatbot一些tools(下文会详细讲tool)，让它能够上网搜索东西、编辑文件、运行命令行，恭喜你已经实现了agent，相关实现已经在[`examples/chatbot_with_tools`](./examples/chatbot_with_tools)
   - 总结：**workflow = node + node**、**chatbot = workflow + loop**、 **agent = chatbot + tools = workflow + loop + tools**
   - 恭喜你已经懂Agent了！可能你现在会有疑惑“这么简单的一个轻框架能有用吗，为什么选择 自己造轻框架 而不是 LangChain / Dify / Coze / Google ADK / Spring AI”，
   并且我并没有看到过有人用langchain开发出来好产品，以及langchain还出过非常严重安全漏洞 [CVE-2025-68664](https://github.com/advisories/GHSA-c67j-w6g6-q2cm)，以及存在过度抽象、依赖地狱、bug多、不灵活难以定制等问题。事实上优秀的agent都是采用自己搭建轻框架来开发的，例如[claude-code](https://code.claude.com/docs/zh-CN/overview)、[cursor](https://cursor.com/)、[kimi-cli](https://platform.moonshot.cn/docs/overview)、[pi-mono](https://github.com/badlogic/pi-mono)、[Pocketflow-examples](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook)等等，所以非常推荐自己搭建轻框架或者直接调用llm api来开发。

3. 实现 RAG （阅读需约1小时）
   - 选择 [Chroma](https://docs.trychroma.com/docs/overview/getting-started) 而不是Milvus、LanceDB、pgvector等等，因为Chroma部署简单、api简洁使用成本低
   - 注意，你可能需要一个 embedding model api 而不是 llm api，你可以在Kimi、智谱等官网找到对应的 embedding 模型
   - 恭喜你已经学会了rag！！！
   - 为什么这就是全部了，真有这么简单？是的这就是全部，当初提出 RAG(Retrieval-Augmented Generation) 概念时，可能觉得得有 检索-增强-生成 这三个功能。
   - 但实际上大伙最终只用到了检索，VectorDB 就能很完美执行这个任务
   - 所以 RAG 是个很过时的概念，大伙只想要一个 VectorDB 而已，或者说 RAG=VectorDB

4. 实现 Tool、MCP、Skill （阅读需约1小时）
   - Tool: process call (function call)，也就是调用了一个函数
   - MCP: remote process call 也就是后端里面的 RPC 概念，调用了服务器上的一个函数
   - Skill: local process call 也就是调用了本地的一个函数
   - 它们其实本质上都是 Tool
   - 为什么Tool会有这么多形式？这就不得不说Tool的发展历程。
   - Tool来源：在早期大伙为了chatbot不只是chat，而是实际做些事所以出现了Tool，实现Tool的形式各不一样，最常见的就是输入llm的prompt中里面加入function（等同于tool）的name、parameters、description并且要求llm输出json格式，最后再调用对应的function。
   - MCP来源：为了解决Tool实现参差不齐的现象，anthropic定了一个Tool的标准，也就是[MCP(Model Context Protocol)](https://modelcontextprotocol.io/docs/getting-started/intro)（感觉不如叫Remote Tool Protocol更易读），让各个Tool能够远程“即插即用”，看起来非常棒只要提供了MCP服务就能实现ai从just chat到do something的转变，于是2025年各个公司疯狂都在推行自己的MCP服务
   - Skill来源：但人们渐渐发现了MCP的弊端：每次调用llm时候，都会把在prompt额外加上MCP的所有Tool的信息（包括name、parameters、description等等），发现大部分MCP服务并没有想象的那么有用，以及导致性能变差以及token浪费，anthropic在blog描述了这件事 [Code execution with MCP: Building more efficient agents](https://www.anthropic.com/engineering/code-execution-with-mcp)，并分享了它们的解决方案，就是**渐进式加载**和**多用代码执行**，后来anthropic发布了[skill](https://support.claude.com/en/articles/12512176-what-are-skills)就和这个差不多，重点就是**渐进式加载**和**多用代码执行**。
   - 设计Tool：实际Agent并不需要那么多五花八门的Tool，最重要的是linux中的bash、edit、find、grep、ls、read、write命令，这些就已经能做很多事且做得非常好，Vercel[通过移除大部分的Tool反而提高了text-to-sql从80%到100%](https://vercel.com/blog/we-removed-80-percent-of-our-agents-tools)，以及pi-mono极简coding-agent作者提到[这四个工具就是构建有效 Coding Agent 所需的全部：read、write、edit、bash](https://mariozechner.at/posts/2025-11-30-pi-coding-agent/)
   - 实践：可以阅读[`tools`](./tools)和[`examples/chatbot_with_tools`](./examples/chatbot_with_tools)文件夹里的实现
   - 总结: MCP是Remote Tool，Skill是Local Tool，尽量不要设计Tool并且优先用linux的bash来解决问题

5. 实现 Context / Memory（阅读需约1分钟）
   - 短期 Context：最近几轮的完整对话
   - 长期 Context：更早的对话，会"总结一次"进行压缩
   - Memory = 短期 Context + 长期 Context

6. 实现 Multi-Agent / Subagent / Agent Teams （阅读需约1小时）
   - multi-agent最初设想用google制定的A2A(agent to agent)协议，让不同地方的Agent进行交互，但这个设想失败了，multi-agent效果复杂且大部分性能还不如简单的single agent，且现实中没看到过agent用A2A协议进行交互
   - 但大伙发现有些场景可以用multi-agent来实现上下文隔离、只回传压缩结果、避免主上下文被工具细节污染，这样能提高agent的效果，可以看这个blog了解multi-agent到底是什么[How we built our multi-agent research system](https://www.anthropic.com/engineering/built-multi-agent-research-system)
   - subagent概念由此发展出来，甚至推出了[自定义subagent](https://code.claude.com/docs/zh-CN/sub-agents)。但我并不推荐自定义subagent，毕竟由master agent来自动生成subagent总是个简单高效的选择
   - Agent Teams则是目前最前沿的发展方向，摒弃了主从的agent结构，而采用并行的方式，能够成倍效率且agent间不冲突地开发项目，这是十分有价值的，大伙都在研究，可以参考claude的[agent-teams](https://code.claude.com/docs/zh-CN/agent-teams)以及blog [Building a C compiler with a team of parallel Claudes](https://www.anthropic.com/engineering/building-c-compiler) 还有cursor的blog [扩展长时间运行的自主编码能力](https://cursor.com/cn/blog/scaling-agents) 和 [迈向自动驾驶代码库](https://cursor.com/cn/blog/self-driving-codebases)
   - 顺便一提Agent Teams可以通过Tmux来实现简单且效果非常好！可以看这个文章[What I learned building an opinionated and minimal coding agent](https://mariozechner.at/posts/2025-11-30-pi-coding-agent/)里面的tmux部分

7. 阅读和理解 [pi-mono](https://github.com/badlogic/pi-mono) （阅读需约4小时）
   - Openclaw项目的底层就是pi-mono，pi-mono就是世界上开源里最好的coding-agent
   - 你为什么应该学习这个 coding-agent 项目，因为 coding-agent经过时代的发展已经成为了通用 agent，它可以几乎做任何事情且效果很好
   - 一定要看 blog [What I learned building an opinionated and minimal coding agent](https://mariozechner.at/posts/2025-11-30-pi-coding-agent/)
   - clone pi-mono，然后使用你的claude、cursor等等ai来分析整个项目的结构并且要求有mermaid图写到md里，你就能理解pi-mono它内部是怎样的，顺便一提不推荐看具体源码因为都是vibe coding没什么好看，想知道pi-mono的什么就让ai来告诉你

8. 把 pi-mono 改造成 你的 OpenClaw（阅读约1小时）
   - git clone https://github.com/badlogic/pi-mono.git
   - 安装 pm2: 后台长期运行且崩溃后自动重启 `npm install -g pm2`
   - 因为pi-mono写了hardcode强制用opus-4.5，我们要自定义模型的BASE_URL和模型id，所以修改./pi-mono/packages/mom/src/agent.ts，`const model = getModel("anthropic", "claude-sonnet-4-5");`在这行下面写
```
model.id = process.env.ANTHROPIC_MODEL_ID || "claude-sonnet-4-5";
if (process.env.ANTHROPIC_BASE_URL) model.baseUrl = process.env.ANTHROPIC_BASE_URL;
```
   - 准备好你的llm api，你需要添加下面环境变量，下面是以[kimi](https://www.moonshot.cn)举例，
```
export ANTHROPIC_MODEL_ID=kimi-k2.5
export ANTHROPIC_BASE_URL=https://api.moonshot.cn/anthropic
export ANTHROPIC_API_KEY=sk-m7q...
```
   - 参考 im 接入方式[slack-bot-minimal-guide](https://github.com/badlogic/pi-mono/blob/main/packages/mom/docs/slack-bot-minimal-guide.md)，后面会更新飞书接入方式
   - 运行`npm install`，然后启动`pm2 start packages/mom/dist/main.js --name mom --interpreter node -- --sandbox=host ./packages/mom/data`
   - 恭喜你！你已经打造了属于你自己的OpenClaw，你可以去到Slack上与你的OpenClaw聊

### 额外内容：达到面试/实习要求 （学习需约 2天 * 8小时）

如果你需要找Agent相关工作或者实习，又或者为了更深刻理解Agent，一定要看这一部分。
PS: 已经很多同学通过看我的教程找到了实习。
1. 了解面试都会问什么，以及项目推荐（阅读需约1小时）
   - agent 面试只问项目，没有八股
   - 问你的项目，推荐实现你的 Openclaw，项目名字就写XXXClaw，例如我就写PoiClaw。具体为实现 pi-mono 和调用 pm2 以及 im 接口，clone pimono然后使用你的cursor、claude或其他ai工具，让它分析pi-mono整体架构流程看看分为哪些模块，然后你阅读和理解这些模块，vide coding出来，最终你能实现一个属于你自己的coding-agent，然后使用pm2让它长期跑以及接入im。（可能需要2天 * 8小时来完成）
   - 可能会问以下内容，所以你需要知道整个流程运转（但不一定要实践出来）：Agent 效果可评估、提示词自动优化、Agentic Sandbox、Agent Teams
   - 推荐编写简历的开源免费网站rxresu.me
   - 注意不要写智能客服项目(langchain/dify + rag)，这真的很过时了
   - 已经足够去实习面试了


2. 关注 Agent 效果可评估 与 提示词自动优化（阅读需约15分钟）
   - [agent 效果可评估（较难）](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
   - 提示词自动优化的设计思路和上面这个 blog 差不多，需要设计指标并观测

3. 关注 Agent Teams（阅读需约15分钟）
   - [Agent Teams 概念](https://code.claude.com/docs/en/agent-teams) 以及 blog [Building a C compiler with a team of parallel Claudes](https://www.anthropic.com/engineering/building-c-compiler)
   - [扩展长时间运行的自主编码能力（较难）](https://cursor.com/cn/blog/scaling-agents) 和 [迈向自动驾驶代码库（较难）](https://cursor.com/cn/blog/self-driving-codebases)

4. 了解 Sandbox（阅读需约15分钟）
   - 用过 docker 就行了，使用docker作为sandbox可以应对绝大多数场景
   - 部分对延时要求非常高的场景，需要做专门的agentic infra来优化延时（太复杂了了解下就好）
   - 推荐阅读 [为本地代理实现安全沙箱](https://cursor.com/cn/blog/agent-sandboxing)
