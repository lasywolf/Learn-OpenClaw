"""Chatbot with Memory - 带记忆、上下文管理和Goal Loop的对话机器人"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.goal import GoalState
from core.llm import call_llm
from core.node import Node, Flow, shared
from core.memory import Memory
from tools import get_tools, ToolExecutor

SYSTEM_PROMPT = (
    "你是一个会调用工具的助手。"
    "当问题涉及最新信息、模型版本、产品发布时间或事实核验时，优先调用 search 工具，再基于搜索结果回答。"
    "若问题是本地文件/代码相关，优先使用 read/grep/find/ls 等本地工具。"
)


def get_last_user_input(memory: Memory) -> str:
    for message in reversed(memory.messages):
        if message.get("role") == "user":
            return message.get("content", "")
    return ""


class ChatNode(Node):
    """发送消息给 LLM，获取响应（可能包含 tool_calls）"""

    def exec(self, payload: Any) -> Tuple[str, Any]:
        memory = shared["memory"]
        tools = shared["tools"]
        goal = shared["goal"]

        # [Goal] 未进入 Goal 时，先让 LLM 判断是否需要持续执行。
        if not goal.active:
            # 判断阶段只传入用户最新输入。
            assistant_message = call_llm(messages=goal.build_judge_messages(get_last_user_input(memory)))
            goal.try_start(assistant_message)
            memory.after_llm_response(assistant_message)
            return "output", assistant_message

        # [Goal] 进入 Goal 后，使用带工具的正常 Agent 流程。
        system_prompt = goal.run_prompt(SYSTEM_PROMPT)
        messages = memory.build_context(system_prompt=system_prompt)
        assistant_message = call_llm(messages=messages, tools=tools)
        goal.add_usage(assistant_message)

        if assistant_message.get("tool_calls"):
            memory.add_raw_message(assistant_message)
            return "tool_call", assistant_message

        memory.after_llm_response(assistant_message)
        goal.try_complete(assistant_message)

        return "output", assistant_message


class ToolCallNode(Node):
    """执行 LLM 返回的 tool_calls"""

    def exec(self, payload: Any) -> Tuple[str, Any]:
        response = payload
        memory = shared["memory"]
        executor = shared["tool_executor"]

        tool_calls = executor.parse_tool_calls(response)
        results = executor.execute_all(tool_calls)

        for tc, result in zip(tool_calls, results):
            print(f"  [Tool] 执行: {tc.name}({tc.arguments})")
            print(f"  [Tool] 结果: {result.content[:100]}...")
            memory.add_raw_message(result.to_message())

        return "chat", None


class OutputNode(Node):
    """输出助手回复，并通过 Memory 自动管理上下文"""

    def exec(self, payload: Any) -> Tuple[str, Any]:
        response = payload
        content = response.get("content", "")
        print(f"\n🤖 Assistant: {content}\n")
        return "default", None


def run_chat() -> None:
    """运行对话循环"""
    print("=" * 60)
    print("🤖 Chatbot with Memory")
    print("=" * 60)
    print("可用工具: read, write, edit, bash, grep, find, ls, search")
    print("记忆管理: 短期上下文 + 长期记忆 (自动压缩)")
    print("持续任务模式: 大模型自动判断是否需要持续执行")
    print("输入 'quit' 或 'exit' 退出\n")

    shared.clear()

    shared["memory"] = Memory()
    shared["tools"] = [t.to_llm_format() for t in get_tools()]
    shared["tool_executor"] = ToolExecutor()

    # [Goal] 初始化并加载持久化 Goal 状态。
    shared["goal"] = GoalState.load()

    chat = ChatNode()
    tool_call = ToolCallNode()
    output = OutputNode()

    chat - "tool_call" >> tool_call
    tool_call - "chat" >> chat
    chat - "output" >> output

    while True:
        user_input = input("👤 You: ").strip()

        goal = shared["goal"]
        memory = shared["memory"]

        if user_input.lower() in ("quit", "exit", "q"):
            print("\n再见！")
            break

        if not user_input:
            continue

        memory.add_message("user", user_input)
        flow = Flow(chat)
        flow.run(None)

        # [Goal] 如果刚才的回复进入了 Goal，则持续运行直到完成或暂停。
        while goal.should_continue():
            print(f"\n🔄 Goal Iteration {goal.current_iter + 1}")
            before_tokens = goal.used_tokens
            try:
                flow = Flow(chat)
                flow.run(None)
            except Exception as exc:
                goal.pause()
                print(f"\n⚠️ Goal 因错误暂停: {exc}\n")
                break
            goal.after_iteration(before_tokens)
            if goal.active:
                memory.add_message("user", goal.continue_message())


def main() -> None:
    if not os.environ.get("OPENAI_API_KEY") or not os.environ.get("OPENAI_BASE_URL"):
        print("⚠️  提示：请先设置环境变量 OPENAI_API_KEY 和 OPENAI_BASE_URL")
        return

    run_chat()


if __name__ == "__main__":
    main()
