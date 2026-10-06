"""
JSON schemas for the agent's tools.

The model only sees these schemas.
Write descriptions for a junior engineer.
Bad descriptions cause bad tool choices.
"""

from agent.tools import get_new_papers, save_digest


GET_NEW_PAPERS_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_new_papers",
        "description": (
            "Search arXiv for recent papers on a topic. "
            "Filters out papers already shown to the user. "
            "Summarizes each new paper with the LLM. "
            "Adds the papers to the current run. "
            "Returns the count and titles. "
            "Call this once per topic."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "A short topic string. Example: 'agents'.",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of papers to fetch. Default 5.",
                    "default": 5,
                },
            },
            "required": ["topic"],
        },
    },
}


SAVE_DIGEST_SCHEMA = {
    "type": "function",
    "function": {
        "name": "save_digest",
        "description": (
            "Write a Markdown digest file for all papers collected "
            "in the current run. Takes no arguments. "
            "Call this exactly once, after all get_new_papers calls."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
}


TOOLS = [GET_NEW_PAPERS_SCHEMA, SAVE_DIGEST_SCHEMA]


TOOL_REGISTRY = {
    "get_new_papers": get_new_papers,
    "save_digest": save_digest,
}
