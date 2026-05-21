import json
import os
from typing import List, Dict, Callable, Any


# ---------- 长期记忆 ----------
class LongTermMemory:
    """管理 MEMORY.md 作为持久化笔记。保存重要事件、用户偏好等全局重要信息"""
    def __init__(self, filepath: str = ".\chat_memory\MEMORY.md"):
        self.filepath = filepath
        # 确保目录存在
        dir_name = os.path.dirname(self.filepath)
        if dir_name:  # 避免空字符串（文件就在当前目录时）
            os.makedirs(dir_name, exist_ok=True)
        if not os.path.exists(self.filepath):
            with open(self.filepath, "w", encoding="utf-8") as f:
                f.write("# 长期记忆，包括用户偏好、重要事件等等\n\n")

    def read(self) -> str:
        with open(self.filepath, "r", encoding="utf-8") as f:
            return f.read()

    def write(self, content: str):
        with open(self.filepath, "w", encoding="utf-8") as f:
            f.write(content)

    def append(self, text: str):
        with open(self.filepath, "a", encoding="utf-8") as f:
            f.write("\n" + text)

# ---------- 短期记忆 ----------
class ShortTermMemory:
    """短期记忆类：存储对话上下文，并且达到上下文阈值时可进行摘要压缩"""
    def __init__(self,
                 filepath: str = ".\chat_memory\session.json", # 短期记忆持久化文件存储路径
                 max_context_length: int = 4096, # llm最大上下文token数
                 compress_threshold: float = 0.9, # 触发摘要压缩的阈值
                 keep_messages_on_compress: int = 4, # 摘要压缩后保留的完整对话轮数
                 long_term_memory: LongTermMemory = None # 长期记忆类
                 ):
        self.filepath = filepath
        # 确保目录存在
        dir_name = os.path.dirname(self.filepath)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        self.max_context_length = max_context_length
        self.compress_threshold = compress_threshold
        self.messages: List[Dict[str, str]] = []
        self.last_usage_total: int = 0
        self.keep_messages_on_compress = keep_messages_on_compress
        self.long_term_memory = long_term_memory
        self._load()

    def _load(self):
        if os.path.exists(self.filepath):
            with open(self.filepath, "r", encoding="utf-8") as f:
                try:
                    self.messages = json.load(f)
                except json.JSONDecodeError:
                    self.messages = []

    def _save(self):
        dir_name = os.path.dirname(self.filepath)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.messages, f, ensure_ascii=False, indent=2)

    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        self._save()

    def update_usage(self, total_tokens: int):
        self.last_usage_total = total_tokens

    def needs_compression(self) -> bool:
        if self.max_context_length <= 0:
            return False
        return (self.last_usage_total / self.max_context_length) > self.compress_threshold

    def compress_with_llm(self, llm_call: Callable[..., Dict[str, Any]]):
        """
        使用 call_llm 进行压缩：
        call_llm 必须接收 messages 参数，返回包含 "content" 字段的字典。
        """
        # 保留最后若干轮对话
        keep_count = max(2, min(self.keep_messages_on_compress, len(self.messages) - 2))
        to_compress = self.messages[:-keep_count]
        recent = self.messages[-keep_count:]

        prompt = self._build_compress_prompt(to_compress)

        # 调用 call_llm（使用其标准签名）
        response = llm_call(messages=prompt)
        llm_response_text = response.get("content", "")

        # 解析 LLM 返回的 JSON
        try:
            result = json.loads(llm_response_text)
            summary = result.get("summary", "")
            memory_update = result.get("memory_update", "")
        except json.JSONDecodeError:
            summary = llm_response_text
            memory_update = ""

        # 更新短期记忆
        compressed = [{"role": "system", "content": f"对话历史摘要：\n{summary}"}] + recent
        self.messages = compressed
        self._save()

        # 更新长期记忆
        if memory_update and self.long_term_memory:
            self.long_term_memory.append(memory_update)

    def _build_compress_prompt(self, old_messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """构建压缩提示词（内部已含 system 消息，直接喂给 call_llm）。"""
        history_text = "\n".join([f"{m['role']}: {m['content']}" for m in old_messages])

        system_prompt = (
            "你是一个对话压缩助手。请对以下对话历史生成摘要，并判断是否有值得长期记住的信息。\n"
            "请以 JSON 格式返回，包含两个字段：\n"
            "  1. summary: 对话历史的简洁摘要（保留关键信息，如任务、决定、使用的工具、偏好等）。\n"
            "  2. memory_update: 如果有新的值得长期记忆的信息（如用户偏好、重要事实、新知识），"
            "请以一句话描述；如果没有新信息，返回空字符串。\n"
            "只返回 JSON，不要附加任何其他文本。"
        )
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请压缩以下对话历史：\n{history_text}"}
        ]

    def build_context(self, system_prompt: str = "") -> List[Dict[str, str]]:
        """构建最终发给主 LLM 的消息列表。"""
        msgs = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        for m in self.messages:
            if msgs and msgs[-1]["role"] == "system" and m["role"] == "system":
                msgs[-1]["content"] += "\n\n" + m["content"]
            else:
                msgs.append(m)
        return msgs

    def after_llm_response(
        self,
        assistant_content: str,
        total_tokens: int,
        llm_call: Callable[..., Dict[str, Any]],
    ):
        """
        LLM 调用后必须调用的回调：
        1. 记录助手回复
        2. 更新 token 用量
        3. 若需要，自动执行压缩（内部会调用 llm_call 生成摘要）
        """
        # 1. 添加助手消息
        self.add_message("assistant", assistant_content)

        # 2. 更新最近一次的总 token 消耗
        self.update_usage(total_tokens)

        # 3. 判断压缩
        if self.needs_compression():
            self.compress_with_llm(llm_call)
