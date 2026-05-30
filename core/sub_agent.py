from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from core.llm import call_llm


TaskStatus = Literal["pending", "running", "done", "failed"]

SUB_AGENT_SYSTEM_PROMPT = (
    "你是一个只负责完成子目标的 sub-agent。"
    "你只能基于当前子目标回答，有自己独立的上下文。"
    "请输出简洁、可被父 agent 汇总的结果。"
)


@dataclass
class SubAgentTask:
    id: int
    goal: str
    status: TaskStatus = "pending"
    result: str = ""
    error: str = ""


class SubAgent:
    def run(self, sub_goal: str) -> str:
        messages = [{"role": "user", "content": f"请完成这个子目标：{sub_goal}"}]
        response = call_llm(messages=messages, system_prompt=SUB_AGENT_SYSTEM_PROMPT)
        return (response.get("content") or "").strip()


class SubAgentManager:
    def __init__(self, sub_agent: SubAgent | None = None) -> None:
        self.sub_agent = sub_agent or SubAgent()
        self.tasks: list[SubAgentTask] = []

    def create_tasks(self, sub_goals: list[str]) -> list[SubAgentTask]:
        clean_goals = [goal.strip() for goal in sub_goals if goal.strip()]
        self.tasks = [SubAgentTask(id=index + 1, goal=goal) for index, goal in enumerate(clean_goals)]
        return self.tasks

    def run_all(self) -> list[SubAgentTask]:
        for task in self.tasks:
            self.run_task(task)
        return self.tasks

    def run_task(self, task: SubAgentTask) -> None:
        task.status = "running"
        try:
            task.result = self.sub_agent.run(task.goal) or "sub-agent 没有返回内容。"
            task.status = "done"
        except Exception as exc:
            task.error = str(exc)
            task.status = "failed"
