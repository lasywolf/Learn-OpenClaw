"""Chatbot with MCP - 通过 MCP 协议调用远程工具的对话机器人"""

from __future__ import annotations

import asyncio
import os
import sys
import threading
from concurrent.futures import Future
from pathlib import Path
from typing import Any, Awaitable, Callable, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.llm import call_llm
from core.node import Node, Flow, shared
from tools.executor import ToolCall
from tools.mcp.client import MCPClient

PROJECT_ROOT = Path(__file__).parent.parent.parent

SYSTEM_PROMPT = (
    "你是一个会调用 MCP 工具的助手，可用工具全部来自 MCP 服务器。"
    "当问题涉及最新信息、模型版本、产品发布时间或事实核验时，优先先调用 search 工具，再基于搜索结果回答。"
    "涉及数值计算时，优先调用 add/multiply 工具，再基于结果回答。"
)


class MCPClientRunner:
    """在后台线程的事件循环中运行 MCPClient，向同步的 Node 提供同步接口。

    MCP 客户端是 async 的，而 Node/Flow 是同步的，
    所以用一个常驻事件循环线程桥接两者。
    注意：anyio 的 cancel scope 必须在同一个 task 里进入和退出，
    因此所有 MCP 操作都通过队列交给同一个 worker 任务串行执行。
    """

    def __init__(self) -> None:
        self._client = MCPClient()
        self._loop = asyncio.new_event_loop()
        self._queue: asyncio.Queue = asyncio.Queue()
        self._worker: asyncio.Task | None = None
        self._closed = False
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()
        asyncio.run_coroutine_threadsafe(self._start_worker(), self._loop).result()

    async def _start_worker(self) -> None:
        self._worker = asyncio.create_task(self._work())

    async def _work(self) -> None:
        """worker 任务：串行执行提交进来的所有 MCP 操作"""
        while True:
            coro_fn, future = await self._queue.get()
            if coro_fn is None:  # 停止信号
                break
            try:
                future.set_result(await coro_fn())
            except BaseException as exc:
                future.set_exception(exc)

    def _run(self, coro_fn: Callable[[], Awaitable[Any]]) -> Any:
        """把协程工厂提交给 worker 任务，阻塞等待结果"""
        future: Future = Future()
        self._loop.call_soon_threadsafe(self._queue.put_nowait, (coro_fn, future))
        return future.result()

    def connect_stdio(
        self,
        command: str,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
    ) -> None:
        self._run(lambda: self._client.connect_stdio(command, args, env))

    def list_tools(self) -> list[dict]:
        return self._run(self._client.list_tools)

    def call_tool(self, name: str, arguments: dict) -> Any:
        return self._run(lambda: self._client.call_tool(name, arguments))

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            self._run(self._client.close)
        finally:
            # 停止 worker 任务和后台事件循环
            asyncio.run_coroutine_threadsafe(self._shutdown(), self._loop).result(timeout=5)
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._thread.join(timeout=5)

    async def _shutdown(self) -> None:
        await self._queue.put((None, None))
        if self._worker is not None:
            await self._worker
            self._worker = None


def mcp_tools_to_llm_format(mcp_tools: list[dict]) -> list[dict]:
    """把 MCP 的 Tool 定义转换为 OpenAI function calling 格式"""
    return [
        {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool.get("description") or "",
                "parameters": tool.get("input_schema") or {"type": "object", "properties": {}},
            },
        }
        for tool in mcp_tools
    ]


def mcp_result_to_text(result: Any) -> str:
    """把 MCP CallToolResult 的 content 拼接为文本"""
    parts = []
    for block in result.content:
        text = getattr(block, "text", None)
        parts.append(text if text else block.model_dump_json())
    return "\n".join(parts)


class ChatNode(Node):
    """调用 LLM，打印 assistant content，并按 tool_calls 决定是否继续。"""

    def exec(self, payload: Any) -> Tuple[str, Any]:
        messages = shared["messages"]
        tools = shared["tools"]

        assistant_message = call_llm(messages=messages, tools=tools, system_prompt=SYSTEM_PROMPT)
        messages.append(assistant_message)

        content = assistant_message["content"]
        tool_calls = assistant_message.get("tool_calls")

        if content:
            print(f"\n🤖 Assistant: {content}\n")

        if tool_calls:
            return "tool_call", assistant_message

        return "done", assistant_message


class ToolCallNode(Node):
    """通过 MCP 协议执行 LLM 返回的 tool_calls"""

    def exec(self, payload: Any) -> Tuple[str, Any]:
        response = payload
        messages = shared["messages"]
        mcp = shared["mcp_client"]

        tool_calls = [ToolCall.from_openai_item(item) for item in response.get("tool_calls", [])]

        for tc in tool_calls:
            print(f"  [MCP] 调用: {tc.name}({tc.arguments})")
            result = mcp.call_tool(tc.name, tc.arguments)
            content = mcp_result_to_text(result)
            if getattr(result, "is_error", False):
                content = f"Error: {content}"
            print(f"  [MCP] 结果: {content[:100]}...")
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": content,
            })

        return "chat", None


def run_chat() -> None:
    """运行对话循环"""
    print("=" * 60)
    print("🤖 Chatbot with MCP")
    print("=" * 60)

    mcp = MCPClientRunner()
    shared.clear()
    shared["messages"] = []

    chat = ChatNode()
    tool_call = ToolCallNode()

    chat - "tool_call" >> tool_call
    tool_call - "chat" >> chat

    try:
        # 连接 MCP 服务器 (stdio 子进程)
        # mcp 2.x 的子进程默认不继承 PYTHONPATH，需显式传入才能 import 项目里的 tools.builtins
        mcp.connect_stdio(
            command=sys.executable,
            args=[str(PROJECT_ROOT / "tools" / "mcp" / "server.py")],
            env={"PYTHONPATH": str(PROJECT_ROOT)},
        )
        shared["mcp_client"] = mcp
        shared["tools"] = mcp_tools_to_llm_format(mcp.list_tools())

        print("MCP 服务器: tools/mcp/server.py (stdio)")
        print("可用 MCP 工具:", ", ".join(t["function"]["name"] for t in shared["tools"]))
        print("输入 'quit' 或 'exit' 退出\n")

        while True:
            user_input = input("👤 You: ").strip()

            if user_input.lower() in ("quit", "exit", "q"):
                print("\n再见！")
                break

            if not user_input:
                continue

            shared["messages"].append({"role": "user", "content": user_input})
            flow = Flow(chat)
            flow.run(None)
    finally:
        mcp.close()


def main() -> None:
    if not os.environ.get("OPENAI_API_KEY") or not os.environ.get("OPENAI_BASE_URL"):
        print("⚠️  提示：请先设置环境变量 OPENAI_API_KEY 和 OPENAI_BASE_URL")
        return

    run_chat()


if __name__ == "__main__":
    main()
