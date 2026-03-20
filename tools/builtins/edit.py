"""编辑文件工具 - 精确文本替换"""

from __future__ import annotations

from pathlib import Path


def edit_file(path: str, old_text: str, new_text: str, cwd: str | None = None) -> dict:
    """
    编辑文件，用 new_text 替换 old_text。

    Args:
        path: 文件路径
        old_text: 要查找的文本（必须完全匹配）
        new_text: 新文本
        cwd: 工作目录

    Returns:
        包含 diff 和 first_changed_line 的字典
    """
    if cwd:
        file_path = Path(cwd) / path
    else:
        file_path = Path(path)

    file_path = file_path.resolve()

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    content = file_path.read_text(encoding="utf-8")

    # 检查 old_text 是否存在
    if old_text not in content:
        raise ValueError(f"Could not find the exact text in {path}. The old text must match exactly.")

    # 检查是否唯一
    occurrences = content.count(old_text)
    if occurrences > 1:
        raise ValueError(f"Found {occurrences} occurrences of the text in {path}. The text must be unique.")

    # 执行替换
    new_content = content.replace(old_text, new_text, 1)

    if content == new_content:
        raise ValueError(f"No changes made to {path}.")

    # 写入文件
    file_path.write_text(new_content, encoding="utf-8")

    # 生成简单的 diff
    old_lines = content.split("\n")
    new_lines = new_content.split("\n")

    first_changed_line = None
    for i, (old, new) in enumerate(zip(old_lines, new_lines)):
        if old != new:
            first_changed_line = i + 1
            break

    return {
        "message": f"Successfully replaced text in {path}",
        "first_changed_line": first_changed_line,
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 3:
        try:
            result = edit_file(sys.argv[1], sys.argv[2], sys.argv[3])
            print(result)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Usage: python edit.py <file_path> <old_text> <new_text>", file=sys.stderr)
