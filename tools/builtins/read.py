"""读取文件工具"""

from __future__ import annotations

from pathlib import Path


DEFAULT_MAX_BYTES = 30 * 1024  # 30KB
DEFAULT_MAX_LINES = 2000


def read_file(
    path: str,
    offset: int | None = None,
    limit: int | None = None,
    cwd: str | None = None,
) -> str:
    """
    读取文件内容。

    Args:
        path: 文件路径（相对或绝对）
        offset: 起始行号（1-indexed）
        limit: 最大读取行数
        cwd: 工作目录

    Returns:
        文件内容文本
    """
    if cwd:
        file_path = Path(cwd) / path
    else:
        file_path = Path(path)

    file_path = file_path.resolve()

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if not file_path.is_file():
        raise ValueError(f"Not a file: {path}")

    # 读取内容
    content = file_path.read_text(encoding="utf-8")
    lines = content.split("\n")
    total_lines = len(lines)

    # 应用 offset (1-indexed 转 0-indexed)
    start_line = max(0, (offset or 1) - 1)

    if start_line >= total_lines:
        raise ValueError(f"Offset {offset} is beyond end of file ({total_lines} lines total)")

    # 应用 limit
    if limit is not None:
        end_line = min(start_line + limit, total_lines)
    else:
        end_line = total_lines

    selected_lines = lines[start_line:end_line]
    result = "\n".join(selected_lines)

    # 截断处理
    result_bytes = result.encode("utf-8")
    if len(result_bytes) > DEFAULT_MAX_BYTES:
        # 找到截断位置
        truncated = result_bytes[:DEFAULT_MAX_BYTES].decode("utf-8", errors="ignore")
        # 找到最后一个完整行
        last_newline = truncated.rfind("\n")
        if last_newline > 0:
            truncated = truncated[:last_newline]
        result = truncated
        end_line = start_line + truncated.count("\n") + 1
        result += f"\n\n[Showing lines {start_line + 1}-{end_line} of {total_lines} ({DEFAULT_MAX_BYTES // 1024}KB limit). Use offset={end_line + 1} to continue.]"
    elif limit is not None and end_line < total_lines:
        result += f"\n\n[{total_lines - end_line} more lines in file. Use offset={end_line + 1} to continue.]"

    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        try:
            content = read_file(sys.argv[1])
            print(content)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Usage: python read.py <file_path>", file=sys.stderr)
