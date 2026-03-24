"""Simple Chatbot - 简单对话机器人（无工具）"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.llm import call_llm
from core.node import Node, Flow, shared

SYSTEM_PROMPT = "你是一个友好的对话助手，请回答用户的问题。"


class ChatNode(Node):
    """对话节点：发送消息给 LLM 并获取回复"""

    def exec(self, payload: Any) -> Tuple[str, Any]:
        messages = shared["messages"]
        assistant_message = call_llm(messages=messages, system_prompt=SYSTEM_PROMPT)
        messages.append(assistant_message)
        return "output", assistant_message


class OutputNode(Node):
    """输出节点：显示助手回复"""

    def exec(self, payload: Any) -> Tuple[str, Any]:
        response = payload
        content = response.get("content", "")
        print(f"\n🤖 Assistant: {content}\n")
        return "default", None


def run_chat() -> None:
    """运行对话循环"""
    print("=" * 60)
    print("🤖 Simple Chatbot")
    print("=" * 60)
    print("输入 'quit' 或 'exit' 退出\n")

    # 初始化
    shared.clear()
    shared["messages"] = []

    # 创建节点
    chat = ChatNode()
    output = OutputNode()

    # 连接节点
    chat - "output" >> output

    while True:
        # 获取用户输入
        user_input = input("👤 You: ").strip()

        if user_input.lower() in ("quit", "exit", "q"):
            print("\n再见！")
            break

        if not user_input:
            continue

        # 添加用户消息
        shared["messages"].append({"role": "user", "content": user_input})

        # 运行 Flow
        flow = Flow(chat)
        flow.run(None)


def main() -> None:
    if not os.environ.get("OPENAI_API_KEY") or not os.environ.get("OPENAI_BASE_URL"):
        print("⚠️  提示：请先设置环境变量 OPENAI_API_KEY 和 OPENAI_BASE_URL")
        return

    run_chat()


if __name__ == "__main__":
    main()
