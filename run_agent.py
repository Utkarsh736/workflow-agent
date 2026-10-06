"""
Entry point for the agent.

Usage:
    uv run run_agent.py "Find new papers on agents and evals. Save a digest."
"""

import sys
from dotenv import load_dotenv
load_dotenv()

from agent.loop import run_agent


def main():
    if len(sys.argv) < 2:
        print("Usage: uv run run_agent.py \"<your request>\"")
        sys.exit(1)

    user_message = " ".join(sys.argv[1:])
    print(f"[user] {user_message}")
    print("-" * 60)

    final = run_agent(user_message)

    print("-" * 60)
    print(f"[agent] {final}")


if __name__ == "__main__":
    main()
