"""Tool executor for parsing and running LLM tool calls."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.builtins import get_builtin_tools


@dataclass(slots=True)
class ToolCall:
    """A normalized tool call parsed from an assistant message."""

    id: str
    name: str
    arguments: dict[str, Any]

    @classmethod
    def from_openai_item(cls, item: dict[str, Any]) -> "ToolCall":
        """Parse one OpenAI-style tool call item."""
        function = item.get("function", {})
        arguments = function.get("arguments", {})
        if isinstance(arguments, str):
            arguments = _safe_json_loads(arguments)
        if not isinstance(arguments, dict):
            arguments = {}
        return cls(
            id=item.get("id", ""),
            name=function.get("name", ""),
            arguments=arguments,
        )


@dataclass(slots=True)
class ToolResult:
    """Result of one tool execution."""

    tool_call_id: str
    content: str
    is_error: bool = False

    def to_message(self) -> dict[str, str]:
        """Convert to a standard tool message for conversation history."""
        return {
            "role": "tool",
            "tool_call_id": self.tool_call_id,
            "content": self.content,
        }


class ToolExecutor:
    """Parse assistant messages and execute referenced tools."""

    def __init__(self) -> None:
        self.tools = get_builtin_tools()
        self.tool_map = {tool.name: tool for tool in self.tools}

    def parse_tool_calls(self, assistant_message: dict[str, Any]) -> list[ToolCall]:
        """
        Parse tool calls from a single assistant message.

        Supported format:
        - OpenAI: message.tool_calls
        """
        openai_calls = assistant_message.get("tool_calls")
        if isinstance(openai_calls, list):
            return [ToolCall.from_openai_item(item) for item in openai_calls]

        return []

    def execute(self, tool_call: ToolCall) -> ToolResult:
        """Execute one tool call and normalize the output."""
        tool = self.tool_map.get(tool_call.name)
        if not tool:
            return ToolResult(
                tool_call_id=tool_call.id,
                content=f"Tool '{tool_call.name}' not found",
                is_error=True,
            )

        try:
            raw_result = tool.execute(**tool_call.arguments)
        except Exception as exc:
            return ToolResult(
                tool_call_id=tool_call.id,
                content=f"Error: {exc}",
                is_error=True,
            )

        return ToolResult(
            tool_call_id=tool_call.id,
            content=_stringify_result(raw_result),
            is_error=False,
        )

    def execute_all(self, tool_calls: list[ToolCall]) -> list[ToolResult]:
        """Execute all tool calls in order."""
        return [self.execute(tool_call) for tool_call in tool_calls]


def _safe_json_loads(value: str) -> Any:
    """Load JSON safely and fall back to empty dict."""
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return {}


def _stringify_result(value: Any) -> str:
    """Convert tool return value to a printable string."""
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def demo() -> None:
    """演示解析和执行"""
    print("=" * 60)
    print("Tool 执行器演示")
    print("=" * 60)

    executor = ToolExecutor()

    # 模拟 LLM 返回的 assistant 消息
    assistant_message: dict[str, Any] = {
        "role": "assistant",
        "content": "我来查看目录",
        "tool_calls": [
            {
                "id": "call_abc123",
                "type": "function",
                "function": {
                    "name": "ls",
                    "arguments": '{"path": "tools"}'
                }
            },
            {
                "id": "call_def456",
                "type": "function",
                "function": {
                    "name": "bash",
                    "arguments": '{"command": "pwd"}'
                }
            }
        ]
    }

    print("\n1. LLM 返回的消息:")
    print(f"   Content: {assistant_message['content']}")
    print(f"   Tool calls: {len(assistant_message['tool_calls'])}")

    # 解析 tool calls
    print("\n2. 解析 tool calls:")
    tool_calls = executor.parse_tool_calls(assistant_message)
    for tc in tool_calls:
        print(f"   - {tc.name}({tc.arguments})")

    # 执行工具
    print("\n3. 执行工具:")
    for tc in tool_calls:
        result = executor.execute(tc)
        print(f"   {tc.name} -> {result.content[:60]}...")

    # 转换为 messages
    print("\n4. 转换为 messages 追加到 context:")
    results = executor.execute_all(tool_calls)
    for r in results:
        msg = r.to_message()
        print(f"   {msg}")


if __name__ == "__main__":
    demo()
