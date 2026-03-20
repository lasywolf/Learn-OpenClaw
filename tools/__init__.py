"""Tools 模块 - 内置工具和 LLM 集成

使用示例:
    from tools import get_tools, execute_tool, chat_with_tools

    # 获取工具列表
    tools = get_tools()

    # 执行单个工具
    result = execute_tool("ls", {"path": "."})

    # 完整对话（自动处理 tool calls）
    response = chat_with_tools("列出当前目录", tools)
"""

from .builtins import get_builtin_tools, Tool
from .executor import ToolExecutor, ToolResult

__all__ = [
    "Tool",
    "get_builtin_tools",
    "ToolExecutor",
    "ToolResult",
    "get_tools",
    "execute_tool",
    "chat_with_tools",
]


def get_tools():
    """获取所有内置工具"""
    return get_builtin_tools()


def execute_tool(name: str, arguments: dict) -> str:
    """执行指定工具"""
    from .builtins import get_builtin_tools

    tools = get_builtin_tools()
    tool_map = {tool.name: tool for tool in tools}
    tool = tool_map.get(name)
    if not tool:
        return f"Error: Tool '{name}' not found"

    try:
        result = tool.execute(**arguments)
        return str(result) if isinstance(result, str) else str(result)
    except Exception as e:
        return f"Error: {e}"


def chat_with_tools(user_input: str, tools=None, system_prompt: str = "") -> str:
    """简单的对话函数（演示用）"""
    import json

    if tools is None:
        tools = get_builtin_tools()

    # 模拟 LLM 处理（实际项目应调用真实 API）
    # 这里根据用户输入简单判断调用哪个工具
    user_lower = user_input.lower()

    if "列出" in user_lower or "ls" in user_lower or "目录" in user_lower:
        # 模拟 LLM 调用 ls
        path = "."
        if "tools" in user_lower:
            path = "tools"
        elif "builtins" in user_lower:
            path = "tools/builtins"

        result = execute_tool("ls", {"path": path})
        return f"目录内容：\n{result}"

    elif "读" in user_lower or "read" in user_lower or "查看" in user_lower:
        # 尝试提取路径
        words = user_input.split()
        path = None
        for w in words:
            if "." in w or "/" in w:
                path = w
                break

        if path:
            result = execute_tool("read", {"path": path})
            return f"文件内容：\n{result[:500]}..."

    return "请输入有效的指令，如：列出 tools 目录、查看 README.md"
