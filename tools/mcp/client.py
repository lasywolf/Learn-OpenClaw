"""MCP 客户端实现 - 使用 FastMCP"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# 添加上级目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPClient:
    """MCP 客户端"""

    def __init__(self) -> None:
        self.session: ClientSession | None = None
        self.tools: list[dict] = []

    async def connect_stdio(self, command: str, args: list[str] | None = None) -> None:
        """通过 stdio 连接到 MCP 服务器"""
        server_params = StdioServerParameters(
            command=command,
            args=args or [],
            env=None,
        )

        async with stdio_client(server_params) as (read, write):
            self.session = ClientSession(read, write)
            await self.session.initialize()

            # 获取可用工具列表
            tools_result = await self.session.list_tools()
            self.tools = [tool.dict() for tool in tools_result.tools]

    async def list_tools(self) -> list[dict]:
        """列出服务器上的所有工具"""
        if not self.session:
            raise RuntimeError("Not connected to server")
        tools_result = await self.session.list_tools()
        return [tool.dict() for tool in tools_result.tools]

    async def call_tool(self, name: str, arguments: dict) -> Any:
        """调用服务器上的工具"""
        if not self.session:
            raise RuntimeError("Not connected to server")
        result = await self.session.call_tool(name, arguments)
        return result

    async def close(self) -> None:
        """关闭连接"""
        if self.session:
            await self.session.close()
            self.session = None


# 示例用法
async def main():
    client = MCPClient()

    # 连接到本地 MCP 服务器
    await client.connect_stdio("python", ["tools/mcp/server.py"])

    # 列出工具
    tools = await client.list_tools()
    print("Available tools:", [t["name"] for t in tools])

    # 调用工具
    result = await client.call_tool("add", {"a": 3, "b": 4})
    print("3 + 4 =", result)

    await client.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
