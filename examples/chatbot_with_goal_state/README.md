# Chatbot with Goal State

这是一个带记忆和 Goal 状态管理的聊天机器人示例。它在 `chatbot_with_memory` 的基础上增加了 `GoalState`，可以让大模型自动判断任务是否需要持续执行。

## 功能

- **工具调用**：支持 read, write, edit, bash, grep, find, ls, search 等工具。
- **对话记忆**：复用 `Memory`，把用户、助手、工具结果等消息保存到 `chat_memory/session.jsonl`。
- **长期记忆**：复用 `MEMORY.md`，保存用户偏好、重要事实、运行环境等信息。
- **Goal 状态**：把当前目标、执行轮数、token 用量等保存到 `chat_memory/goal_state.json`。
- **自动持续执行**：大模型先判断任务是否需要进入 Goal；进入后会持续调用工具，直到任务完成、达到限制或出现错误。

## 运行

```bash
# 设置环境变量
export OPENAI_API_KEY=your-api-key
export OPENAI_BASE_URL=your-base-url

# 从项目根目录运行
python examples/chatbot_with_goal_state/main.py
```

Windows PowerShell 可以这样设置环境变量：

```powershell
$env:OPENAI_API_KEY="your-api-key"
$env:OPENAI_BASE_URL="your-base-url"
python examples/chatbot_with_goal_state/main.py
```

运行后会自动创建 `chat_memory/` 目录：

- `session.jsonl`：保存完整的对话消息。
- `MEMORY.md`：保存长期记忆。
- `goal_state.json`：保存当前 Goal 的状态，方便程序中断后知道上一次执行到哪里。

## Goal 管理流程

1. 用户正常输入任务，不需要输入特殊命令。
2. 程序先让 LLM 判断这是不是需要持续执行的任务。判断阶段只会传入最新一条用户输入，不会传入历史工具调用记录。
3. 如果只是普通问题，LLM 直接回答，不进入 Goal。
4. 如果需要多轮工具调用、写文件或验证结果，LLM 会返回 `<goal_start>...</goal_start>`，程序进入 Goal 模式。
5. Goal 模式下，程序会循环调用 LLM 和工具，并把中间结果写入记忆。
6. 每轮结束后，`goal_state.json` 会更新执行轮数和 token 用量。
7. 当 LLM 确认任务完成时，会输出 `<goal_complete>`，程序结束 Goal 模式，并清零轮数和 token 用量。

简单理解：`Memory` 负责“记住聊过什么”，`GoalState` 负责“记住当前任务是否还要继续做”。
