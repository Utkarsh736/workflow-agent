"""
Groq LLM client with retry logic.

Wraps the Groq SDK.
Retries on rate limits and service errors.
Logs token usage.
"""

import os
import time
import json
from dataclasses import dataclass

from groq import Groq
from groq import APIStatusError, APIConnectionError


# Groq limits reset per minute. Backoff is shorter than arXiv.
RETRY_BACKOFF_SECONDS = [5, 10, 20]


@dataclass
class LLMResult:
    """Result of one LLM call."""
    text: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    model: str


def _get_client() -> Groq:
    """Create a Groq client from the environment variable."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. "
            "Add it to your .env file."
        )
    return Groq(api_key=api_key)


def chat(
    system: str,
    user: str,
    model: str = "qwen/qwen3.8-27b",
    temperature: float = 0.2,
    max_tokens: int = 300,
    max_retries: int = 3,
    reasoning_effort: str | None = None,
) -> LLMResult:
    """
    Call the Groq chat API.

    Retries on 429 and 503. Raises on other errors.
    Returns LLMResult with text and token counts.
    """
    client = _get_client()
    last_error: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            kwargs = dict(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            if reasoning_effort is not None:
                kwargs["reasoning_effort"] = reasoning_effort

            response = client.chat.completions.create(**kwargs)

            choice = response.choices[0]
            usage = response.usage

            return LLMResult(
                text=(choice.message.content or "").strip(),
                input_tokens=getattr(usage, "prompt_tokens", 0),
                output_tokens=getattr(usage, "completion_tokens", 0),
                total_tokens=getattr(usage, "total_tokens", 0),
                model=model,
            )

        except APIStatusError as e:
            status = e.status_code
            if status not in (429, 503):
                raise
            last_error = e
            if attempt == max_retries:
                break
            wait = RETRY_BACKOFF_SECONDS[attempt]
            print(f"[groq] HTTP {status}. Waiting {wait}s. "
                  f"Attempt {attempt + 1}/{max_retries}.")
            time.sleep(wait)

        except APIConnectionError as e:
            last_error = e
            if attempt == max_retries:
                break
            wait = RETRY_BACKOFF_SECONDS[attempt]
            print(f"[groq] Connection error. Waiting {wait}s.")
            time.sleep(wait)

    raise RuntimeError(
        f"Groq call failed after {max_retries + 1} attempts."
    ) from last_error


# --- Tool-calling chat ---

from dataclasses import dataclass
from typing import Any


@dataclass
class AssistantTurn:
    """
    One assistant turn from the model.

    message: the message dict to append to the conversation.
    text: the assistant's text content (may be empty).
    tool_calls: list of {id, name, arguments}.
    """
    message: dict
    text: str
    tool_calls: list[dict]


def chat_with_tools(
    messages: list[dict],
    tools: list[dict],
    model: str = "qwen/qwen3.8-27b",
    temperature: float = 0.2,
    max_tokens: int = 1024,
    max_retries: int = 3,
) -> AssistantTurn:
    """
    Call Groq with a list of tools.

    Returns an AssistantTurn. The message dict can be appended
    to the conversation. It contains the assistant message and
    any tool_calls, in the format Groq expects.
    """
    client = _get_client()
    last_error: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=temperature,
                max_tokens=max_tokens,
            )
            break
        except APIStatusError as e:
            if e.status_code not in (429, 503):
                raise
            last_error = e
            if attempt == max_retries:
                raise
            wait = RETRY_BACKOFF_SECONDS[attempt]
            print(f"[groq] HTTP {e.status_code}. Waiting {wait}s.")
            time.sleep(wait)
        except APIConnectionError as e:
            last_error = e
            if attempt == max_retries:
                raise
            wait = RETRY_BACKOFF_SECONDS[attempt]
            print(f"[groq] Connection error. Waiting {wait}s.")
            time.sleep(wait)

    msg = response.choices[0].message

    tool_calls: list[dict] = []
    raw_tool_calls = getattr(msg, "tool_calls", None) or []
    for tc in raw_tool_calls:
        tool_calls.append({
            "id": tc.id,
            "name": tc.function.name,
            "arguments": json.loads(tc.function.arguments or "{}"),
        })

    # Build the assistant message for the conversation history.
    assistant_message: dict = {
        "role": "assistant",
        "content": msg.content,
    }
    if raw_tool_calls:
        assistant_message["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in raw_tool_calls
        ]

    return AssistantTurn(
        message=assistant_message,
        text=(msg.content or "").strip(),
        tool_calls=tool_calls,
    )