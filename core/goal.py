import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, ClassVar


@dataclass
class GoalState:
    filepath: ClassVar[Path] = Path(r".\chat_memory\goal_state.json")
    start_marker: ClassVar[str] = "<goal_start>"
    end_marker: ClassVar[str] = "</goal_start>"
    complete_marker: ClassVar[str] = "<goal_complete>"

    objective: str = ""
    status: str = "idle"
    active: bool = False
    current_iter: int = 0
    max_iters: int = 10                 # 最大尝试次数
    token_budget: int = 500_000         # 最大token限制
    used_tokens: int = 0                # 已消耗token

    @classmethod
    def load(cls) -> "GoalState":
        if not cls.filepath.exists():
            return cls()
        return cls(**json.loads(cls.filepath.read_text(encoding="utf-8")))

    def save(self) -> None:
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self.filepath.write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2), encoding="utf-8")

    def reset(self, objective: str) -> None:
        # 新 Goal 从 0 开始统计，避免继承上一个任务的轮数和 token。
        self.objective = objective
        self.status = "active"
        self.active = True
        self.current_iter = 0
        self.used_tokens = 0

    def pause(self, status: str = "paused") -> None:
        self.active = False
        self.status = status
        self.save()

    def judge_prompt(self) -> str:
        return (
            "你现在只负责判断最新一条用户消息是否需要进入 Goal 模式。"
            "不要执行任务，不要调用工具，不要输出 tool_calls、DSML 或 JSON。"
            "如果只是普通问题，直接回答。"
            "如果任务需要多轮工具调用、代码修改、文件写入、验证或持续推进，"
            f"只能输出 {self.start_marker}清晰的目标描述{self.end_marker}，不要输出其他文字。"
        )

    def build_judge_messages(self, user_input: str) -> list[dict[str, str]]:
        # [Goal] 判断阶段只看用户的最新一条输入，避免历史 tool_calls 干扰模型输出格式。
        return [
            {"role": "system", "content": self.judge_prompt()},
            {"role": "user", "content": user_input},
        ]

    def run_prompt(self, base_prompt: str) -> str:
        return (
            base_prompt
            + "对于长期任务（如写代码、修 bug、重构、调查并写文件），不要中途停止，应持续执行直到真正完成。"
            + "修改代码或写入文件后应主动验证结果（如 test/build/lint/read/ls）。"
            + "任务未完成不要停止。"
            + f"只有确认任务完成时，才单独输出 {self.complete_marker}。"
        )

    def add_usage(self, assistant_message: dict[str, Any]) -> None:
        if self.active:
            self.used_tokens += assistant_message.get("usage", {}).get("total_tokens", 0)

    def parse_start(self, content: str) -> str:
        if self.start_marker not in content or self.end_marker not in content:
            return ""
        return content.split(self.start_marker, 1)[1].split(self.end_marker, 1)[0].strip()

    def try_start(self, assistant_message: dict[str, Any]) -> bool:
        if self.active:
            return False
        objective = self.parse_start(assistant_message.get("content", "") or "")
        if not objective:
            return False

        # 判断阶段只负责启动 Goal，真正的工具调用会在下一轮循环发生。
        self.reset(objective)
        self.save()
        assistant_message["content"] = f"已进入 Goal 模式：{objective}"
        return True

    def try_complete(self, assistant_message: dict[str, Any]) -> bool:
        if not self.active or self.complete_marker not in (assistant_message.get("content", "") or ""):
            return False

        # 完成后保留 objective 作为记录，但清空当前任务的统计数据。
        self.active = False
        self.status = "complete"
        self.current_iter = 0
        self.used_tokens = 0
        self.save()
        print("\n✅ Goal completed.\n")
        return True

    def should_continue(self) -> bool:
        if not self.active:
            return False

        # 保护示例程序，避免模型一直不输出 complete 时无限循环。
        if self.current_iter >= self.max_iters:
            print("\n⚠️ 达到最大迭代次数，已暂停。\n")
            self.pause()
            return False
        if self.used_tokens >= self.token_budget:
            print("\n⚠️ 达到 Token 上限，已暂停。\n")
            self.pause("budget_limited")
            return False
        return True

    def after_iteration(self, before_tokens: int) -> None:
        self.current_iter += 1
        self.save()
        print(f"📊 Tokens: +{self.used_tokens - before_tokens} (Total: {self.used_tokens}/{self.token_budget})")

    def continue_message(self) -> str:
        return (
            f"继续当前目标：{self.objective}\n不要重复之前失败的方法。"
            "如果修改了代码，请主动验证结果（如 test/build/lint）。"
            f"任务未完成不要停止。确认完成后单独输出 {self.complete_marker}"
        )

