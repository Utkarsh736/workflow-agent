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


# --- Tool 2: summarize_paper ---

from agent.llm import chat, chat_stream
from agent.prompts import SUMMARIZE_SYSTEM, summarize_user


def summarize_paper(
    title: str,
    abstract: str,
    model: str = "qwen/qwen3.8-27b",
    max_tokens: int = 300,
    temperature: float = 0.2,
    reasoning_effort: str | None = "none",
) -> dict[str, Any]:
    """
    Summarize one paper with the Groq LLM.

    Returns a dict with:
    - summary: the bullet text
    - input_tokens, output_tokens, total_tokens
    - model
    """
    result = chat_stream(
        system=SUMMARIZE_SYSTEM,
        user=summarize_user(title, abstract),
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        reasoning_effort=reasoning_effort,
    )
    return {
        "summary": result.text,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
        "total_tokens": result.total_tokens,
        "model": result.model,
    }


# --- Agent-facing tools ---

from datetime import date
from pathlib import Path

from agent.sessions import add_papers, get_papers, reset_run
from agent.config import load_config
from agent.memory import check_seen, mark_seen


_CONFIG_CACHE: dict | None = None


def _config() -> dict:
    """Load config once and cache it."""
    global _CONFIG_CACHE
    if _CONFIG_CACHE is None:
        _CONFIG_CACHE = load_config()
    return _CONFIG_CACHE


def get_new_papers(topic: str, max_results: int = 5) -> dict[str, Any]:
    """
    Agent-facing tool.

    Search arXiv for a topic. Filter seen papers.
    Summarize each new paper. Append to the current run.
    Return a small summary (count and titles).
    """
    cfg = _config()
    db_path = cfg["db_path"]

    papers = search_arxiv(topic, max_results=max_results)

    new_papers: list[dict] = []
    for paper in papers:
        if check_seen(paper["id"], db_path=db_path):
            continue

        result = summarize_paper(
            title=paper["title"],
            abstract=paper["abstract"],
            model=cfg["llm_model"],
            max_tokens=cfg["llm_max_tokens"],
            temperature=cfg["llm_temperature"],
        )
        paper["summary"] = result["summary"]
        paper["tokens"] = result["total_tokens"]

        mark_seen(paper["id"], paper["title"], db_path=db_path)
        new_papers.append(paper)

    total = add_papers(new_papers)

    return {
        "topic": topic,
        "new_in_this_call": len(new_papers),
        "run_total": total,
        "titles": [p["title"] for p in new_papers],
    }


def save_digest() -> dict[str, Any]:
    """
    Agent-facing tool.

    Write a Markdown digest for all papers collected in the current run.
    """
    papers = get_papers()
    if not papers:
        return {
            "skipped": True,
            "reason": "No new papers in this run. Nothing to save.",
        }

    cfg = _config()
    today = date.today().isoformat()
    digest_dir = Path(cfg["digest_dir"])
    digest_dir.mkdir(parents=True, exist_ok=True)
    out_path = digest_dir / f"{today}.md"

    lines: list[str] = []
    lines.append(f"# arXiv Digest — {today}")
    lines.append("")
    lines.append(f"{len(papers)} new papers.")
    lines.append("")

    for p in papers:
        lines.append(f"## {p['title']}")
        lines.append("")
        lines.append(f"- URL: {p['url']}")
        lines.append(f"- Published: {p['published']}")
        lines.append("")
        lines.append(p["summary"])
        lines.append("")
        lines.append("---")
        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")

    return {"path": str(out_path), "count": len(papers)}