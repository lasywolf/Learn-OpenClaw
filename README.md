[中文版 README](./README-zh.md)

# What Can This Tutorial Do for You?
Learn agent fundamentals from scratch in one day (about 9 hours)! I wrote this tutorial to show that agents are actually very simple.
It can also help you land an agent-related job or internship. Quite a few students have already found internships after following this tutorial, and it has been very well received in study groups, so now I am open-sourcing it for everyone.

## Overview

### Learn Agent Basics (about 1 day * 9 hours)

1. Get your own LLM API key (about 15 minutes)
   - You may need to learn some Python and [uv](https://docs.astral.sh/uv/getting-started/installation/). It is written in Rust, similar to Cargo in the Rust ecosystem, and it is extremely fast.
   - Why use `uv` instead of Conda: `uv` is open source and has no commercial licensing risk. Conda has [potential commercial licensing issues](https://www.anaconda.com/blog/is-conda-free) for organizations with more than 200 people.
   - You will probably need an LLM API key. I recommend [Kimi](https://platform.moonshot.cn/docs/overview) or [Zhipu](https://open.bigmodel.cn).
   - Configure `OPENAI_API_KEY` and `OPENAI_BASE_URL`, then try running [`core/llm.py`](./core/llm.py).

2. Implement Node / Workflow / Agent (about 1 hour)
   - Our final goal is to build an agent that can search the web, run shell commands, and edit files.
   - At the core, an agent can be abstracted with Nodes. I have already prepared a minimal implementation for you in [`core/node.py`](./core/node.py). It takes fewer than 60 lines to build a lightweight agent framework, and it is very easy to understand. If you do not have much Python background, you can paste the code into an AI tool and ask it to explain it.
   - But how do we actually use Nodes? You can create 3 Nodes and connect them to implement `receive input -> search the web -> have the model generate a summary`. Congratulations, you have built a workflow. The relevant implementation is in [`examples/workflow`](./examples/workflow).
   - Now create another workflow for `receive user input -> model responds`, then loop it repeatedly. Congratulations, you have built a chatbot. The implementation is in [`examples/chatbot`](./examples/chatbot).
   - Next, give the chatbot some tools (explained in more detail below) so it can search the web, edit files, and run shell commands. Congratulations, you have built an agent. The implementation is in [`examples/chatbot_with_tools`](./examples/chatbot_with_tools).
   - Summary: **workflow = node + node**, **chatbot = workflow + loop**, **agent = chatbot + tools = workflow + loop + tools**
   - Congratulations, you already understand agents. You might still wonder, "Can such a simple lightweight framework really be useful? Why choose to build your own lightweight framework instead of LangChain / Dify / Coze / Google ADK / Spring AI?"
   In practice, I have not really seen people build great products with LangChain, and it has also had severe security issues such as [CVE-2025-68664](https://github.com/advisories/GHSA-c67j-w6g6-q2cm). It also tends to suffer from over-abstraction, dependency hell, too many bugs, and poor flexibility. In reality, strong agents are usually built on self-made lightweight frameworks, such as [Claude Code](https://code.claude.com/docs/en/overview), [Cursor](https://cursor.com/), [kimi-cli](https://platform.moonshot.cn/docs/overview), [pi-mono](https://github.com/badlogic/pi-mono), and [Pocketflow-examples](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook). That is why I strongly recommend building your own lightweight framework or directly using the LLM API.

3. Implement RAG (about 1 hour)
   - Choose [Chroma](https://docs.trychroma.com/docs/overview/getting-started) instead of Milvus, LanceDB, pgvector, and so on, because Chroma is easy to deploy, has a clean API, and is cheap to use.
   - Note that you may need an embedding model API rather than an LLM API. You can find embedding models on platforms such as Kimi and Zhipu.
   - Congratulations, you already understand RAG.
   - Is that really all? Is it really this simple? Yes, it is. When the term RAG (Retrieval-Augmented Generation) was first introduced, it sounded like you needed retrieval, augmentation, and generation.
   - But in practice, most people only end up using retrieval, and a vector database handles that perfectly well.
   - So RAG is really an outdated term. What people actually want is just a VectorDB, or in other words, RAG = VectorDB.

4. Implement Tools, MCP, and Skills (about 1 hour)
   - Tool: a process call (function call), meaning you invoke a function.
   - MCP: a remote process call, basically the RPC concept from backend systems, where you call a function on a server.
   - Skill: a local process call, meaning you call a local function.
   - Fundamentally, they are all tools.
   - Why are there so many forms of tools? To answer that, we need to look at how tools evolved.
   - Origin of Tools: early on, people wanted chatbots to do more than just chat, so tools emerged. Different systems implemented them in different ways. The most common pattern was to put the tool's `name`, `parameters`, and `description` into the LLM prompt and ask the model to return JSON, then call the corresponding function.
   - Origin of MCP: to solve the inconsistency in tool implementations, Anthropic proposed a standard called [MCP (Model Context Protocol)](https://modelcontextprotocol.io/docs/getting-started/intro). Frankly, something like "Remote Tool Protocol" might be more readable. The idea was that tools could become remotely "plug and play", which sounded great. As long as someone exposed an MCP service, AI could move from "just chat" to "do something". Because of that, in 2025, many companies rushed to launch their own MCP services.
   - Origin of Skills: later, people gradually realized the downside of MCP. Every time the LLM was called, the prompt also had to include all the MCP tool metadata such as `name`, `parameters`, and `description`. It turned out that many MCP services were not nearly as useful as expected, and they also hurt performance and wasted tokens. Anthropic described this in [Code execution with MCP: Building more efficient agents](https://www.anthropic.com/engineering/code-execution-with-mcp), and shared a solution centered on **progressive loading** and **using code execution more often**. Later Anthropic released [skills](https://support.claude.com/en/articles/12512176-what-are-skills), which follow a very similar idea. The key is still **progressive loading** and **using code execution more often**.
   - Designing Tools: in practice, agents do not need a huge variety of fancy tools. The most important ones are the Linux basics: `bash`, `edit`, `find`, `grep`, `ls`, `read`, and `write`. These are already enough to do many things very well. Vercel even found that [removing most of their tools improved text-to-sql accuracy from 80% to 100%](https://vercel.com/blog/we-removed-80-percent-of-our-agents-tools). The author of the ultra-minimal coding agent pi-mono also wrote that [these four tools are all you need for an effective coding agent: read, write, edit, bash](https://mariozechner.at/posts/2025-11-30-pi-coding-agent/).
   - Practice: you can read the implementations in [`tools`](./tools) and [`examples/chatbot_with_tools`](./examples/chatbot_with_tools).
   - Summary: MCP is a Remote Tool, Skill is a Local Tool. Try not to over-design tools, and prefer solving problems with Linux `bash` whenever possible.

5. Implement Context / Memory (about 1 minute)
   - Short-term context: the complete recent conversation turns.
   - Long-term context: earlier conversations, compressed after being summarized once.
   - Memory = short-term context + long-term context

6. Implement Multi-Agent / Subagent / Agent Teams (about 1 hour)
   - The original multi-agent idea was to use Google's A2A (agent-to-agent) protocol so agents in different places could talk to each other, but this idea largely failed. Multi-agent systems are often complex, and in many cases they perform worse than a simple single agent. In real-world usage, I have barely seen agents actually communicate through A2A.
   - However, people found that some scenarios do benefit from multi-agent setups: context isolation, returning only compressed results, and preventing the main context from being polluted by tool details. This can improve agent performance. You can read [How we built our multi-agent research system](https://www.anthropic.com/engineering/built-multi-agent-research-system) to understand what multi-agent is really about.
   - The concept of the subagent grew out of this, and eventually people even introduced [custom subagents](https://code.claude.com/docs/en/sub-agents). I do not really recommend custom subagents, because having the master agent automatically generate subagents is usually the simpler and more effective choice.
   - Agent Teams are now the cutting edge direction. Instead of using a master-slave structure, they work in parallel, allowing much higher efficiency and fewer conflicts while developing projects. This is highly valuable, and many people are researching it. You can refer to Claude's [agent-teams](https://code.claude.com/docs/en/agent-teams), the blog [Building a C compiler with a team of parallel Claudes](https://www.anthropic.com/engineering/building-c-compiler), and Cursor's blogs [Scaling long-running autonomous coding agents](https://cursor.com/blog/scaling-agents) and [Towards self-driving codebases](https://cursor.com/blog/self-driving-codebases).
   - By the way, Agent Teams can also be implemented very simply and effectively with Tmux. See the Tmux section in [What I learned building an opinionated and minimal coding agent](https://mariozechner.at/posts/2025-11-30-pi-coding-agent/).

7. Read and understand [pi-mono](https://github.com/badlogic/pi-mono) (about 4 hours)
   - The foundation of the Openclaw project is pi-mono, and pi-mono is the best open-source coding agent in the world.
   - Why should you study this coding-agent project? Because coding agents have evolved into general-purpose agents. They can do almost anything and often do it very well.
   - You should definitely read the blog [What I learned building an opinionated and minimal coding agent](https://mariozechner.at/posts/2025-11-30-pi-coding-agent/).
   - Clone pi-mono, then use Claude, Cursor, or other AI tools to analyze the entire project structure and ask them to produce a Mermaid diagram in Markdown. That way you can understand how pi-mono works internally. By the way, I do not recommend reading all of the source code in detail because much of it is vibe-coded and not especially worth studying line by line. If you want to know how pi-mono works, let AI explain the parts you care about.

8. Turn pi-mono into your own OpenClaw (about 1 hour)
   - `git clone https://github.com/badlogic/pi-mono.git`
   - Install pm2 for long-running background processes and automatic restarts: `npm install -g pm2`
   - Because pi-mono hardcodes `opus-4.5`, if you want to use a custom model `BASE_URL` and model id, edit `./pi-mono/packages/mom/src/agent.ts` and add the following right below `const model = getModel("anthropic", "claude-sonnet-4-5");`
```
model.id = process.env.ANTHROPIC_MODEL_ID || "claude-sonnet-4-5";
if (process.env.ANTHROPIC_BASE_URL) model.baseUrl = process.env.ANTHROPIC_BASE_URL;
```
   - Prepare your LLM API credentials. Here is a [Kimi](https://www.moonshot.cn) example:
```
export ANTHROPIC_MODEL_ID=kimi-k2.5
export ANTHROPIC_BASE_URL=https://api.moonshot.cn/anthropic
export ANTHROPIC_API_KEY=sk-m7q...
```
   - Refer to this IM integration guide: [slack-bot-minimal-guide](https://github.com/badlogic/pi-mono/blob/main/packages/mom/docs/slack-bot-minimal-guide.md). A Feishu integration guide will be added later.
   - In `pi-mono`, run `npm install`, then start it with `pm2 start packages/mom/dist/main.js --name mom --interpreter node -- --sandbox=host ./packages/mom/data`
   - Congratulations. You have now built your own OpenClaw, and you can chat with it on Slack.

### Extra: Reach Interview / Internship Level (about 2 days * 8 hours)

If you want an agent-related job or internship, or just want a deeper understanding of agents, you should definitely read this section.
PS: many students have already landed internships after following this tutorial.

1. Understand what interviews ask, and what projects to build (about 1 hour)
   - Agent interviews mainly ask about projects, not rote memorization.
   - For your project, I recommend building your own OpenClaw. Just name it something like `XXXClaw`. For example, mine is `PoiClaw`. In practice, this means implementing pi-mono and integrating pm2 plus an IM interface. Clone pi-mono, then use Cursor, Claude, or other AI tools to analyze its high-level architecture and figure out its main modules. Read and understand those modules, then vibe-code your own version. In the end, you will have your own coding agent, then use pm2 to keep it running and connect it to an IM platform. This may take about 2 days * 8 hours.
   - You may also get asked about the following, so you should understand the overall flow even if you do not build everything yourself: agent evaluation, prompt auto-optimization, agentic sandboxing, and Agent Teams.
   - I recommend the open-source resume site rxresu.me.
   - Do not put a customer service bot project (`langchain/dify + rag`) on your resume. That is really outdated.
   - At that point, you are already in a good position for internship interviews.

2. Pay attention to agent evaluation and prompt auto-optimization (about 15 minutes)
   - [Agent evaluation for AI agents (advanced)](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
   - Prompt auto-optimization follows a similar design philosophy: define metrics and observe them continuously.

3. Pay attention to Agent Teams (about 15 minutes)
   - [Agent Teams concept](https://code.claude.com/docs/en/agent-teams) and the blog [Building a C compiler with a team of parallel Claudes](https://www.anthropic.com/engineering/building-c-compiler)
   - [Scaling long-running autonomous coding agents (advanced)](https://cursor.com/cn/blog/scaling-agents) and [Towards self-driving codebases (advanced)](https://cursor.com/cn/blog/self-driving-codebases)

4. Understand Sandbox (about 15 minutes)
   - If you have used Docker, that is already enough. Docker as a sandbox can handle the vast majority of cases.
   - Some scenarios with extremely strict latency requirements need dedicated agentic infrastructure to optimize latency, but that is complicated and only worth understanding at a high level.
   - Recommended reading: [Sandboxing local agents securely](https://cursor.com/cn/blog/agent-sandboxing)
