"""
Tools for the workflow-agent.

Each tool is a plain Python function.
Each tool returns structured data.
Each tool is safe to call many times.
"""

import time
import arxiv
from typing import Any


# --- Safety layer: rate limiter ---

class ArxivRateLimiter:
    """
    Enforce the arXiv API rate limit.

    arXiv allows 1 request every 3 seconds.
    We wait 3 seconds between requests.
    We never make parallel requests.
    """

    def __init__(self, min_interval_seconds: float = 3.0):
        self.min_interval = min_interval_seconds
        self.last_request_time: float = 0.0

    def wait(self) -> None:
        """Block until it is safe to make the next request."""
        now = time.monotonic()
        elapsed = now - self.last_request_time
        if elapsed < self.min_interval:
            sleep_time = self.min_interval - elapsed
            print(f"[rate-limit] waiting {sleep_time:.1f}s before next request")
            time.sleep(sleep_time)
        self.last_request_time = time.monotonic()


# One shared limiter for the whole process.
# This prevents parallel calls from different functions.
_limiter = ArxivRateLimiter(min_interval_seconds=3.0)


# --- Safety layer: retry with backoff ---

def _retry_with_backoff(func, max_retries: int = 3):
    """
    Call func. On HTTP 429, wait and retry.

    Backoff schedule: 30s, 60s, 120s.
    After max_retries, raise the error.
    """
    backoff_seconds = [30, 60, 120]
    for attempt in range(max_retries + 1):
        try:
            return func()
        except arxiv.HTTPError as e:
            if e.status != 429:
                raise
            if attempt == max_retries:
                raise
            wait = backoff_seconds[attempt]
            print(f"[backoff] HTTP 429. Waiting {wait}s. Attempt {attempt + 1}/{max_retries}.")
            time.sleep(wait)


# --- Tool 1: search_arxiv ---

def search_arxiv(topic: str, max_results: int = 5) -> list[dict[str, Any]]:
    """
    Search arXiv for recent papers on a topic.

    Args:
        topic: A search string. Example: "agents" or "transformer".
        max_results: Maximum number of papers to return. Default 5.

    Returns:
        A list of paper dictionaries. Each dictionary has:
        id, title, abstract, published, url, authors.
    """
    _limiter.wait()

    query = f"cat:cs.AI AND {topic}"

    def _do_search():
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
        )
        client = arxiv.Client()
        results = []
        for paper in client.results(search):
            results.append({
                "id": paper.entry_id.split("/")[-1],
                "title": paper.title.strip(),
                "abstract": paper.summary.strip()[:800],
                "published": str(paper.published.date()),
                "url": paper.entry_id,
                "authors": [a.name for a in paper.authors],
            })
        return results

    return _retry_with_backoff(_do_search)
