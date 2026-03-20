"""目录列表工具"""

from __future__ import annotations

from pathlib import Path


DEFAULT_LIMIT = 500
DEFAULT_MAX_BYTES = 30 * 1024


def ls(path: str | None = None, limit: int | None = None, cwd: str | None = None) -> str:
    """
    列出目录内容。

    Args:
        path: 目录路径（默认当前目录）
        limit: 最大条目数
        cwd: 工作目录

    Returns:
        目录内容列表
    """
    if cwd:
        dir_path = Path(cwd) / (path or ".")
    else:
        dir_path = Path(path or ".")

    dir_path = dir_path.resolve()

    if not dir_path.exists():
        raise FileNotFoundError(f"Path not found: {dir_path}")

    if not dir_path.is_dir():
        raise ValueError(f"Not a directory: {dir_path}")

    effective_limit = limit or DEFAULT_LIMIT

    try:
        entries = list(dir_path.iterdir())
    except PermissionError:
        raise PermissionError(f"Cannot read directory: {dir_path}")

    # 按字母顺序排序（不区分大小写）
    entries.sort(key=lambda e: e.name.lower())

    results = []
    entry_limit_reached = False

    for entry in entries:
        if len(results) >= effective_limit:
            entry_limit_reached = True
            break

        suffix = "/" if entry.is_dir() else ""
        results.append(entry.name + suffix)

    if not results:
        return "(empty directory)"

    output = "\n".join(results)

    if len(output.encode("utf-8")) > DEFAULT_MAX_BYTES:
        result_bytes = output.encode("utf-8")
        output = result_bytes[:DEFAULT_MAX_BYTES].decode("utf-8", errors="ignore")
        output += f"\n\n[{DEFAULT_MAX_BYTES // 1024}KB limit reached]"

    if entry_limit_reached:
        output += f"\n\n[{effective_limit} entries limit reached. Use limit={effective_limit * 2} for more]"

    return output


if __name__ == "__main__":
    import sys

    try:
        result = ls(sys.argv[1] if len(sys.argv) > 1 else None)
        print(result)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
