"""
In-memory session store for one agent run.

Design:
- There is one current run at a time.
- get_new_papers appends papers to the current run.
- save_digest reads the current run.
- The model never sees a session_id. It cannot lose data.

This is process-local. If the process restarts, the run is lost.
That is fine for Phase 1. Phase 3 will persist runs.
"""


_CURRENT_RUN: list[dict] = []


def reset_run() -> None:
    """Clear the current run. Call this at the start of each agent run."""
    _CURRENT_RUN.clear()


def add_papers(papers: list[dict]) -> int:
    """Append papers to the current run. Return the new total count."""
    _CURRENT_RUN.extend(papers)
    return len(_CURRENT_RUN)


def get_papers() -> list[dict]:
    """Return a shallow copy of the current run's papers."""
    return list(_CURRENT_RUN)


def paper_count() -> int:
    """Return how many papers are in the current run."""
    return len(_CURRENT_RUN)