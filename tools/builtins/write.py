"""写入文件工具"""

from __future__ import annotations

from pathlib import Path


def write_file(path: str, content: str, cwd: str | None = None) -> str:
    """
    写入内容到文件。自动创建父目录。

    Args:
        path: 文件路径（相对或绝对）
        content: 要写入的内容
        cwd: 工作目录

    Returns:
        成功消息
    """
    if cwd:
        file_path = Path(cwd) / path
    else:
        file_path = Path(path)

    file_path = file_path.resolve()

    # 创建父目录
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # 写入文件
    file_path.write_text(content, encoding="utf-8")

    return f"Successfully wrote {len(content)} bytes to {path}"


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 2:
        try:
            result = write_file(sys.argv[1], sys.argv[2])
            print(result)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Usage: python write.py <file_path> <content>", file=sys.stderr)
