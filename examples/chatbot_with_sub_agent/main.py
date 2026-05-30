"""Chatbot with Sub-Agent - 父 agent 拆解目标并调用多个简易 sub-agent"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.llm import call_llm
from core.node import Flow, Node, shared
from core.sub_agent import SubAgentManager, SubAgentTask

PLAN_SYSTEM_PROMPT = (
    "你是父 agent，负责把用户目标拆成 2 到 4 个清晰的子目标。"
    "只输出 JSON 字符串数组，不要输出解释文字。"
)

SUMMARY_SYSTEM_PROMPT = (
    "你是父 agent，负责把多个 sub-agent 的结果汇总成最终回答。"
    "请面向原始目标组织内容，语言清楚，适合初学者阅读。"
)


def parse_sub_goals(text: str, fallback_goal: str) -> list[str]:
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return [fallback_goal]

    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return [fallback_goal]

    if not isinstance(data, list):
        return [fallback_goal]

    sub_goals = [str(item).strip() for item in data if str(item).strip()]
    return sub_goals[:4] or [fallback_goal]


def build_task_report(tasks: list[SubAgentTask]) -> str:
    lines = []
    for task in tasks:
        if task.status == "done":
            lines.append(f"{task.id}. 子目标：{task.goal}\n结果：{task.result}")
        else:
            lines.append(f"{task.id}. 子目标：{task.goal}\n错误：{task.error}")
    return "\n\n".join(lines)


class PlanNode(Node):
    """父 agent 把用户目标拆成 sub-goals"""

    def exec(self, payload: Any) -> Tuple[str, Any]:
        goal = str(payload).strip()
        response = call_llm(messages=[{"role": "user", "content": goal}], system_prompt=PLAN_SYSTEM_PROMPT)
        sub_goals = parse_sub_goals(response.get("content", ""), fallback_goal=goal)

        manager = SubAgentManager()
        tasks = manager.create_tasks(sub_goals)
        shared["goal"] = goal
        shared["manager"] = manager

        print("\n[Sub-goals]")
        for task in tasks:
            print(f"  [{task.id}] {task.status}: {task.goal}")

        return "run", tasks


class RunSubAgentsNode(Node):
    """父 agent 顺序运行 sub-agents，并管理它们的生命周期"""

    def exec(self, payload: Any) -> Tuple[str, Any]:
        manager = shared["manager"]

        print("\n[Running sub-agents]")
        for task in manager.tasks:
            print(f"  [{task.id}] {task.status} -> running: {task.goal}")

        tasks = manager.run_all()

        for task in tasks:
            if task.status == "done":
                print(f"  [{task.id}] done")
            else:
                print(f"  [{task.id}] failed: {task.error}")

        return "summary", tasks


class SummaryNode(Node):
    """父 agent 汇总 sub-agent 的结果"""

    def exec(self, payload: Any) -> Tuple[str, Any]:
        tasks = payload
        goal = shared["goal"]
        report = build_task_report(tasks)
        user_message = f"原始目标：{goal}\n\nsub-agent 结果：\n{report}\n\n请汇总成最终回答。"
        response = call_llm(messages=[{"role": "user", "content": user_message}], system_prompt=SUMMARY_SYSTEM_PROMPT)
        return "output", response


class OutputNode(Node):
    """输出节点：显示助手回复"""

    def exec(self, payload: Any) -> Tuple[str, Any]:
        response = payload
        content = response.get("content", "")
        print(f"\n🤖 Assistant: {content}\n")
        return "default", None


def run_chat() -> None:
    """运行父 agent + sub-agent 示例"""
    print("=" * 60)
    print("🤖 Chatbot with Sub-Agent")
    print("=" * 60)
    print("第一版：LLM-only sub-agent，不接工具、不接记忆、不接 GoalState。")
    print("输入 'quit' 或 'exit' 退出\n")

    shared.clear()

    plan = PlanNode()
    run_sub_agents = RunSubAgentsNode()
    summary = SummaryNode()
    output = OutputNode()

    plan - "run" >> run_sub_agents
    run_sub_agents - "summary" >> summary
    summary - "output" >> output

    while True:
        user_input = input("👤You: ").strip()

        if user_input.lower() in ("quit", "exit", "q"):
            print("\n再见！")
            break

        if not user_input:
            continue

        flow = Flow(plan)
        flow.run(user_input)


def main() -> None:
    if not os.environ.get("OPENAI_API_KEY") or not os.environ.get("OPENAI_BASE_URL"):
        print("提示：请先设置环境变量 OPENAI_API_KEY 和 OPENAI_BASE_URL")
        return

    run_chat()


if __name__ == "__main__":
    main()
