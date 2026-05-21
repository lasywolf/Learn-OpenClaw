from __future__ import annotations

import os
from typing import Any

from openai import OpenAI


def call_llm_simple(prompt: str) -> str:
    """
    简单文本生成接口：输入 prompt，返回字符串。
    """
    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url=os.environ.get("OPENAI_BASE_URL"),
    )
    response = client.chat.completions.create(
        model="kimi-k2.5",
        messages=[{"role": "user", "content": prompt}],
    )
    message = response.choices[0].message
    return message.content or ""


def call_llm(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
    system_prompt: str | None = None,
) -> dict[str, Any]:
    """
    消息/工具模式接口：返回 assistant message 字典。
    """
    msgs = list(messages)

    if system_prompt:
        msgs = [{"role": "system", "content": system_prompt}, *msgs]

    kwargs: dict[str, Any] = {
        "model": "kimi-k2.5",
        "messages": msgs,
    }
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"

    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url=os.environ.get("OPENAI_BASE_URL"),
    )
    response = client.chat.completions.create(**kwargs)
    message = response.choices[0].message

    result: dict[str, Any] = {
        "role": "assistant",
        "content": message.content or "",
        "usage": {
            "total_tokens": response.usage.total_tokens,
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
        },
    }

    reasoning_content = getattr(message, "reasoning_content", None)
    if reasoning_content:
        result["reasoning_content"] = reasoning_content

    if message.tool_calls:
        result["tool_calls"] = [tool_call.model_dump() for tool_call in message.tool_calls]

    return result


if __name__ == "__main__":
    print("Basic:", call_llm_simple("用一句话解释什么是 Agent。"))
