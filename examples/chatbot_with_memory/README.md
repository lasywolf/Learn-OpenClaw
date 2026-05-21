# Chatbot with Memory

带记忆和上下文管理的对话机器人。

## 特性

- **工具调用**：支持 read, write, edit, bash, grep, find, ls, search 等工具
- **短期记忆**：最近几轮完整对话上下文，支持自动压缩
- **长期记忆**：通过 MEMORY.md 持久化保存重要信息
- **自动管理**：每次 LLM 调用后自动记录、更新 token 用量、触发压缩

## 运行

```bash
# 设置环境变量
export OPENAI_API_KEY=your-api-key
export OPENAI_BASE_URL=your-base-url

# 运行
python examples/chatbot_with_memory/main.py
```

## 记忆管理流程

1. 用户提问 → 添加到短期记忆
2. 调用 LLM → 获取回复
3. 如果有 tool_calls → 执行工具 → 循环调用 LLM
4. 最终回复 → 通过 `after_llm_response()` 回调：
   - 记录助手回复
   - 更新 token 用量
   - 若达到压缩阈值（90%），自动调用 LLM 生成摘要
   - 提取值得长期记忆的信息写入 MEMORY.md
