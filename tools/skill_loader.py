"""Skill 加载模块"""

import yaml


def load(path: str) -> tuple[dict, str]:
    """解析 SKILL.md 文件，返回 (metadata, content)。"""
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    if not content.startswith("---"):
        return {}, content

    # 找到第二个 ---
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    metadata = yaml.safe_load(parts[1])
    body = parts[2].strip()

    return metadata or {}, body


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # 默认测试文件（相对于脚本所在目录）
    script_dir = Path(__file__).parent
    test_file = script_dir / "skills/pdf/SKILL.md"

    if len(sys.argv) > 1:
        test_file = Path(sys.argv[1])

    print(f"Loading: {test_file}")
    print("=" * 50)

    meta, body = load(str(test_file))

    print("METADATA:")
    for k, v in meta.items():
        display = f"{v[:60]}..." if isinstance(v, str) and len(v) > 60 else v
        print(f"  {k}: {display}")

    print(f"\nCONTENT (first 300 chars):\n{body[:300]}...")
