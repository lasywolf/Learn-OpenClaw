"""搜索工具"""

from __future__ import annotations

from typing import Any, Dict, List

from ddgs import DDGS


def search(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """使用 DuckDuckGo 搜索网页。"""
    with DDGS() as ddgs:
        return list(ddgs.text(query, max_results=max_results))


if __name__ == "__main__":
    print(search("python programming"))
