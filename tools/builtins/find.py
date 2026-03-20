"""文件查找工具"""

from __future__ import annotations

import subprocess
from pathlib import Path


DEFAULT_LIMIT = 1000
DEFAULT_MAX_BYTES = 30 * 1024


def find(
    pattern: str,
    path: str | None = None,
    limit: int | None = None,
    cwd: str | None = None,
) -> str:
    """
    查找文件。

    Args:
        pattern: glob 模式，如 '*.py', '**/*.json'
        path: 搜索目录（默认当前目录）
        limit: 最大结果数
        cwd: 工作目录

    Returns:
        匹配的文件路径列表
    """
    if cwd:
        search_path = Path(cwd) / (path or ".")
    else:
        search_path = Path(path or ".")

    search_path = search_path.resolve()

    if not search_path.exists():
        raise FileNotFoundError(f"Path not found: {search_path}")

    if not search_path.is_dir():
        raise ValueError(f"Not a directory: {search_path}")

    effective_limit = limit or DEFAULT_LIMIT

    # 尝试使用 fd
    try:
        cmd = [
            "fd",
            "--glob",
            "--color=never",
            "--hidden",
            "--max-results",
            str(effective_limit),
            pattern,
            str(search_path),
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode not in (0, 1):  # fd 返回 1 表示没有匹配
            raise RuntimeError(f"fd failed: {result.stderr}")

        output = result.stdout.strip()

        if not output:
            return "No files found matching pattern"

        lines = output.split("\n")

        # 转换为相对路径
        results = []
        for line in lines:
            line = line.strip()
            if not line:
                continue

            file_path = Path(line)
            try:
                rel_path = file_path.relative_to(search_path)
                results.append(str(rel_path))
            except ValueError:
                results.append(file_path.name)

        result_text = "\n".join(results)

        if len(result_text.encode("utf-8")) > DEFAULT_MAX_BYTES:
            result_bytes = result_text.encode("utf-8")
            result_text = result_bytes[:DEFAULT_MAX_BYTES].decode("utf-8", errors="ignore")
            result_text += f"\n\n[{DEFAULT_MAX_BYTES // 1024}KB limit reached]"

        if len(results) >= effective_limit:
            result_text += f"\n\n[{effective_limit} results limit reached]"

        return result_text

    except FileNotFoundError:
        # 回退到 Python glob
        return _find_python(pattern, search_path, effective_limit)


def _find_python(pattern: str, search_path: Path, limit: int) -> str:
    """Python 实现的 find（回退方案）"""
    results = []

    # 处理 ** 模式
    if "**" in pattern:
        parts = pattern.split("**")
        if len(parts) == 2 and parts[0] == "" and parts[1].startswith("/"):
            # **/pattern
            suffix = parts[1].lstrip("/")
            files = list(search_path.rglob(suffix))
        else:
            files = list(search_path.rglob(pattern))
    else:
        files = list(search_path.glob(pattern))

    for f in files:
        if len(results) >= limit:
            break

        if f.is_file():
            try:
                rel_path = f.relative_to(search_path)
                results.append(str(rel_path))
            except ValueError:
                results.append(f.name)

    if not results:
        return "No files found matching pattern"

    result_text = "\n".join(sorted(results))

    if len(result_text.encode("utf-8")) > DEFAULT_MAX_BYTES:
        result_bytes = result_text.encode("utf-8")
        result_text = result_bytes[:DEFAULT_MAX_BYTES].decode("utf-8", errors="ignore")
        result_text += f"\n\n[{DEFAULT_MAX_BYTES // 1024}KB limit reached]"

    if len(results) >= limit:
        result_text += f"\n\n[{limit} results limit reached]"

    return result_text


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        try:
            result = find(sys.argv[1])
            print(result)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Usage: python find.py <pattern> [path]", file=sys.stderr)
