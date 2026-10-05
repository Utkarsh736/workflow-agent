"""
Groq LLM client with retry logic.

Wraps the Groq SDK.
Retries on rate limits and service errors.
Logs token usage.
"""

import os
import time
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
