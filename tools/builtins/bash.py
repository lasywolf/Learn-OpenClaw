"""Bash 命令执行工具"""

from __future__ import annotations

import subprocess
from pathlib import Path


DEFAULT_MAX_BYTES = 30 * 1024
DEFAULT_MAX_LINES = 2000


def bash(command: str, timeout: int | None = None, cwd: str | None = None) -> dict:
    """
    执行 bash 命令。

    Args:
        command: 要执行的命令
        timeout: 超时时间（秒）
        cwd: 工作目录

    Returns:
        包含 stdout, stderr, exit_code 的字典
    """
    if cwd:
        work_dir = Path(cwd)
    else:
        work_dir = Path.cwd()

    if not work_dir.exists():
        raise FileNotFoundError(f"Working directory does not exist: {work_dir}")

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        output = result.stdout
        if result.stderr:
            output += "\n" + result.stderr if output else result.stderr

        # 截断输出
        lines = output.split("\n")
        if len(lines) > DEFAULT_MAX_LINES:
            lines = lines[-DEFAULT_MAX_LINES:]
            output = "\n".join(lines)
            output = f"[Output truncated to last {DEFAULT_MAX_LINES} lines]\n{output}"

        if len(output.encode("utf-8")) > DEFAULT_MAX_BYTES:
            output_bytes = output.encode("utf-8")
            output = output_bytes[-DEFAULT_MAX_BYTES:].decode("utf-8", errors="ignore")
            output = f"[Output truncated to last {DEFAULT_MAX_BYTES // 1024}KB]\n{output}"

        return {
            "stdout": output,
            "stderr": result.stderr if result.stderr else "",
            "exit_code": result.returncode,
        }

    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": f"Command timed out after {timeout} seconds",
            "exit_code": -1,
        }
    except Exception as e:
        return {
            "stdout": "",
            "stderr": str(e),
            "exit_code": -1,
        }


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        try:
            result = bash(" ".join(sys.argv[1:]))
            print(result["stdout"])
            if result["stderr"]:
                print(result["stderr"], file=sys.stderr)
            sys.exit(result["exit_code"])
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Usage: python bash.py <command>", file=sys.stderr)
