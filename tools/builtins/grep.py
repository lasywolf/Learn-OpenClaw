"""Grep 搜索工具"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


DEFAULT_LIMIT = 100
DEFAULT_MAX_BYTES = 30 * 1024
GREP_MAX_LINE_LENGTH = 1000


def grep(
    pattern: str,
    path: str | None = None,
    glob: str | None = None,
    ignore_case: bool = False,
    literal: bool = False,
    context: int = 0,
    limit: int | None = None,
    cwd: str | None = None,
) -> str:
    """
    搜索文件内容。

    Args:
        pattern: 搜索模式（正则或字面量）
        path: 搜索路径（默认当前目录）
        glob: 文件过滤模式，如 '*.py'
        ignore_case: 忽略大小写
        literal: 将 pattern 视为字面量而非正则
        context: 匹配前后显示的行数
        limit: 最大匹配数
        cwd: 工作目录

    Returns:
        搜索结果文本
    """
    if cwd:
        search_path = Path(cwd) / (path or ".")
    else:
        search_path = Path(path or ".")

    search_path = search_path.resolve()

    if not search_path.exists():
        raise FileNotFoundError(f"Path not found: {search_path}")

    # 尝试使用 ripgrep (rg)
    try:
        cmd = ["rg", "--line-number", "--color=never", "--hidden"]

        if ignore_case:
            cmd.append("--ignore-case")
        if literal:
            cmd.append("--fixed-strings")
        if glob:
            cmd.extend(["--glob", glob])
        if context > 0:
            cmd.extend(["-C", str(context)])

        effective_limit = limit or DEFAULT_LIMIT
        cmd.extend(["--max-count", str(effective_limit)])
        cmd.extend(["-m", str(effective_limit)])
        cmd.append(pattern)
        cmd.append(str(search_path))

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode not in (0, 1):  # rg 返回 1 表示没有匹配
            raise RuntimeError(f"ripgrep failed: {result.stderr}")

        output = result.stdout.strip()

        if not output:
            return "No matches found"

        lines = output.split("\n")

        # 限制行长度
        truncated_lines = []
        lines_truncated = False
        for line in lines:
            if len(line) > GREP_MAX_LINE_LENGTH:
                line = line[:GREP_MAX_LINE_LENGTH] + "..."
                lines_truncated = True
            truncated_lines.append(line)

        output = "\n".join(truncated_lines)

        # 截断输出大小
        if len(output.encode("utf-8")) > DEFAULT_MAX_BYTES:
            output_bytes = output.encode("utf-8")
            output = output_bytes[:DEFAULT_MAX_BYTES].decode("utf-8", errors="ignore")
            output += f"\n\n[{DEFAULT_MAX_BYTES // 1024}KB limit reached]"

        notices = []
        if len(truncated_lines) >= effective_limit:
            notices.append(f"{effective_limit} matches limit reached")
        if lines_truncated:
            notices.append(f"Some lines truncated to {GREP_MAX_LINE_LENGTH} chars")

        if notices:
            output += f"\n\n[{'. '.join(notices)}]"

        return output

    except FileNotFoundError:
        # 回退到 Python 实现
        return _grep_python(
            pattern, search_path, glob, ignore_case, literal, context, limit or DEFAULT_LIMIT
        )


def _grep_python(
    pattern: str,
    search_path: Path,
    glob: str | None,
    ignore_case: bool,
    literal: bool,
    context: int,
    limit: int,
) -> str:
    """Python 实现的 grep（回退方案）"""
    flags = re.IGNORECASE if ignore_case else 0

    if literal:
        pattern = re.escape(pattern)

    regex = re.compile(pattern, flags)

    matches = []
    count = 0

    if search_path.is_file():
        files = [search_path]
    else:
        if glob:
            files = list(search_path.rglob(glob))
        else:
            files = [f for f in search_path.rglob("*") if f.is_file()]

    for file_path in files:
        if count >= limit:
            break

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            lines = content.split("\n")

            for i, line in enumerate(lines, 1):
                if regex.search(line):
                    if count >= limit:
                        break

                    rel_path = file_path.relative_to(search_path) if search_path in file_path.parents else file_path.name

                    if context > 0:
                        start = max(0, i - context - 1)
                        end = min(len(lines), i + context)
                        for j in range(start, end):
                            prefix = f"{rel_path}:{j + 1}:" if j == i - 1 else f"{rel_path}-{j + 1}-"
                            matches.append(f"{prefix} {lines[j]}")
                    else:
                        matches.append(f"{rel_path}:{i}: {line}")

                    count += 1

        except Exception:
            continue

    if not matches:
        return "No matches found"

    output = "\n".join(matches)

    if len(output.encode("utf-8")) > DEFAULT_MAX_BYTES:
        output_bytes = output.encode("utf-8")
        output = output_bytes[:DEFAULT_MAX_BYTES].decode("utf-8", errors="ignore")
        output += f"\n\n[{DEFAULT_MAX_BYTES // 1024}KB limit reached]"

    return output


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        try:
            result = grep(sys.argv[1])
            print(result)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Usage: python grep.py <pattern> [path]", file=sys.stderr)
