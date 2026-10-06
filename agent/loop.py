"""
The agent loop.

This is the core of Phase 1.
The model decides which tool to call.
We execute tools and feed results back.
Loop ends when the model returns no tool calls,
or when we hit MAX_TURNS.
"""

import json
from agent.sessions import reset_run

from agent.llm import chat_with_tools, AssistantTurn
from agent.tool_schemas import TOOLS, TOOL_REGISTRY


MAX_TURNS = 10


AGENT_SYSTEM = """You are a research digest agent.

Your job:
1. Call get_new_papers once for each topic the user asks about.
2. If at least one get_new_papers call returned new papers,
   call save_digest exactly once at the end.
3. If all get_new_papers calls returned zero new papers,
   do NOT call save_digest. Report that nothing was new.

Rules:
- Do not invent paper titles or summaries.
- If a tool returns an error, report it and stop.
- Keep your final message short. One or two sentences.
"""


def run_agent(user_message: str, model: str = "qwen/qwen3.8-27b") -> str:
    """
    Run the agent loop until the model returns a final answer.

    Returns the model's final text.
    """
    reset_run()
    messages: list[dict] = [
        {"role": "system", "content": AGENT_SYSTEM},
        {"role": "user", "content": user_message},
    ]

    for turn in range(1, MAX_TURNS + 1):
        print(f"\n[turn {turn}] calling model...")

        turn_result: AssistantTurn = chat_with_tools(
            messages=messages,
            tools=TOOLS,
            model=model,
        )

        messages.append(turn_result.message)

        if not turn_result.tool_calls:
            print(f"[turn {turn}] model returned final answer")
            return turn_result.text or ""

        for call in turn_result.tool_calls:
            name = call["name"]
            args = call["arguments"]

            print(f"[tool] {name}({args})")

            fn = TOOL_REGISTRY.get(name)
            if fn is None:
                result = {"error": f"unknown tool: {name}"}
            else:
                try:
                    result = fn(**args)
                except Exception as e:
                    result = {"error": f"{type(e).__name__}: {e}"}

            messages.append({
                "role": "tool",
                "tool_call_id": call["id"],
                "content": json.dumps(result),
            })

    return f"Max turns ({MAX_TURNS}) reached. Stopping."
