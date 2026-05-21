"""Chatbot with Memory - 带记忆和上下文管理的对话机器人"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.llm import call_llm
from core.node import Node, Flow, shared
from core.memory import LongTermMemory, ShortTermMemory
from tools import get_tools, ToolExecutor

SYSTEM_PROMPT = (
    "你是一个会调用工具的助手。"
    "当问题涉及最新信息、模型版本、产品发布时间或事实核验时，优先先调用 search 工具，再基于搜索结果回答。"
    "若问题是本地文件/代码相关，优先使用 read/grep/find/ls 等本地工具。"
)


class ChatNode(Node):
    """发送消息给 LLM，获取响应（可能包含 tool_calls）"""

    def exec(self, payload: Any) -> Tuple[str, Any]:
        stm = shared["stm"]
        tools = shared["tools"]

        messages = stm.build_context(system_prompt=SYSTEM_PROMPT)
        assistant_message = call_llm(messages=messages, tools=tools)

        if assistant_message.get("tool_calls"):
            return "tool_call", assistant_message

        return "after_response", assistant_message


class ToolCallNode(Node):
    """执行 LLM 返回的 tool_calls"""

    def exec(self, payload: Any) -> Tuple[str, Any]:
        response = payload
        stm = shared["stm"]
        executor = shared["tool_executor"]

        tool_calls = executor.parse_tool_calls(response)
        results = executor.execute_all(tool_calls)

        for tc, result in zip(tool_calls, results):
            print(f"  [Tool] 执行: {tc.name}({tc.arguments})")
            print(f"  [Tool] 结果: {result.content[:100]}...")
            stm.add_message("tool", result.content)

        return "chat", None


class OutputNode(Node):
    """输出助手回复，并通过 Memory 回调自动管理上下文"""

    def exec(self, payload: Any) -> Tuple[str, Any]:
        response = payload
        content = response.get("content", "")
        print(f"\n🤖 Assistant: {content}\n")
        return "default", None


class MemoryAfterResponseNode(Node):
    """LLM 响应后的 Memory 处理：记录回复、更新 token 用量、触发压缩"""

    def exec(self, payload: Any) -> Tuple[str, Any]:
        response = payload
        stm = shared["stm"]

        assistant_text = response.get("content", "")
        usage_total = response.get("usage", {}).get("total_tokens", 0)

        stm.after_llm_response(assistant_text, usage_total, call_llm)

        return "output", response


def run_chat() -> None:
    """运行对话循环"""
    print("=" * 60)
    print("🤖 Chatbot with Memory")
    print("=" * 60)
    print("可用工具: read, write, edit, bash, grep, find, ls, search")
    print("记忆管理: 短期上下文 + 长期记忆 (自动压缩)")
    print("输入 'quit' 或 'exit' 退出\n")

    shared.clear()

    ltm = LongTermMemory()
    shared["stm"] = ShortTermMemory(
        max_context_length=1024,
        compress_threshold=0.9,
        keep_messages_on_compress=4,
        long_term_memory=ltm,
    )
    shared["tools"] = [t.to_llm_format() for t in get_tools()]
    shared["tool_executor"] = ToolExecutor()

    chat = ChatNode()
    tool_call = ToolCallNode()
    memory_after = MemoryAfterResponseNode()
    output = OutputNode()

    chat - "tool_call" >> tool_call
    tool_call - "chat" >> chat
    chat - "after_response" >> memory_after
    memory_after - "output" >> output

    while True:
        user_input = input("👤 You: ").strip()

        if user_input.lower() in ("quit", "exit", "q"):
            print("\n再见！")
            break

        if not user_input:
            continue

        shared["stm"].add_message("user", user_input)
        flow = Flow(chat)
        flow.run(None)


def main() -> None:
    if not os.environ.get("OPENAI_API_KEY") or not os.environ.get("OPENAI_BASE_URL"):
        print("⚠️  提示：请先设置环境变量 OPENAI_API_KEY 和 OPENAI_BASE_URL")
        return

    run_chat()


if __name__ == "__main__":
    main()
