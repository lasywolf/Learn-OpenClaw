# Chatbot with Memory

这是一个带记忆的聊天机器人示例。它在 `chatbot_with_tools` 的基础上增加了 `Memory`，可以把对话保存下来，并在上下文太长时自动压缩。

## 功能

- **工具调用**：支持 read, write, edit, bash, grep, find, ls, search 等工具。
- **对话记忆**：把用户、助手、工具结果等消息保存到 `chat_memory/session.jsonl`。
- **长期记忆**：把用户偏好、重要事实、运行环境等信息保存到 `chat_memory/MEMORY.md`。
- **自动压缩**：当上下文接近模型上限时，把较早的消息压缩成摘要，并保留最近几条消息。

## 运行

```bash
# 设置环境变量
export OPENAI_API_KEY=your-api-key
export OPENAI_BASE_URL=your-base-url

# 从项目根目录运行
python examples/chatbot_with_memory/main.py
```

Windows PowerShell 可以这样设置环境变量：

```powershell
$env:OPENAI_API_KEY="your-api-key"
$env:OPENAI_BASE_URL="your-base-url"
python examples/chatbot_with_memory/main.py
```

运行后会自动创建 `chat_memory/` 目录：

- `session.jsonl`：保存完整的对话消息，一行是一条 JSON 消息。
- `MEMORY.md`：保存长期记忆，适合放以后也有用的信息。

## 记忆管理流程

1. 用户输入一条消息，写入 `session.jsonl`。
2. 程序把 system prompt、长期记忆、历史对话一起传给 LLM。
3. 如果 LLM 返回 `tool_calls`，程序先保存这条助手消息，再执行工具，并把工具结果也写入记忆。
4. 工具执行完后，再次调用 LLM，直到得到最终文字回复。
5. 最终回复会进入 `after_llm_response()`：保存助手回复、读取本次 token 用量、判断是否需要压缩。
6. 如果 token 数超过阈值，就压缩较早的消息。压缩时会避免拆开一次完整的工具调用消息组。

简单理解：`session.jsonl` 负责保存聊天过程，`MEMORY.md` 负责保存长期有用的信息，自动压缩负责防止上下文越来越长。
