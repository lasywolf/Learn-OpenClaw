from __future__ import annotations
from typing import Any, Dict, Optional, Tuple, Iterable
import time
shared = {}

class Node:
    """
    同步节点：exec(payload) 返回 (action, next_payload)，支持重试。
    """

    def __init__(self, max_retries: int = 1, wait: float = 0) -> None:
        self.successors: Dict[str, "Node"] = {}
        self._action: str = "default"
        self.max_retries, self.wait = max_retries, wait

    def exec(self, payload: Any) -> Tuple[str, Any]:  # pragma: no cover - 需要子类实现
        raise NotImplementedError

    def _exec(self, payload: Any) -> Tuple[str, Any]:
        for cur_retry in range(self.max_retries):
            try:
                return self.exec(payload)
            except Exception as e:
                if cur_retry == self.max_retries - 1:
                    raise e
                if self.wait > 0:
                    time.sleep(self.wait)
        raise RuntimeError("Unexpected error in Node._exec")

    def __rshift__(self, other: "Node") -> "Node":
        self.successors[self._action] = other
        self._action = "default"
        return other

    def __sub__(self, action: str) -> "Node":
        if not isinstance(action, str):
            raise TypeError("Action must be a string")
        self._action = action or "default"
        return self


class Flow:
    """
    同步编排器：按 action 依次执行节点。
    """

    def __init__(self, start: Optional[Node] = None) -> None:
        self.start = start

    def run(self, payload: Any = None) -> Tuple[Optional[str], Any]:
        curr, last_action = self.start, "default"
        while curr:
            last_action, payload = curr._exec(payload)
            curr = curr.successors.get(last_action)
        return last_action, payload
