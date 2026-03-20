"""MCP 服务器实现 - 使用 FastMCP"""

from __future__ import annotations

from fastmcp import FastMCP


# 创建 FastMCP 实例
mcp = FastMCP("agent-tools")


@mcp.tool()
def search(query: str, max_results: int = 5) -> list[dict]:
    """使用 DuckDuckGo 搜索网页"""
    from tools.builtins.search import search as search_impl
    return search_impl(query, max_results)


@mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers"""
    return a + b


@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers"""
    return a * b


# 示例用法
if __name__ == "__main__":
    # 直接运行服务器 (stdio 传输)
    mcp.run(transport="stdio")
