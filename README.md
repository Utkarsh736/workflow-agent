# workflow-agent

An AI agent that automates a boring, painful workflow.

This is a learning project for AI engineering.

## Status

Phase 1: Agent core. Work in progress.

## What it does (Phase 1)

Fetches recent arXiv papers on topics you care about.
Summarizes each paper.
Writes a daily Markdown digest.

## Setup

```bash
uv sync
cp .env.example .env
# Add your GROQ_API_KEY to .env
```

Run (first step)
```bash

uv run run_test.py --topic "agents" --max 3
```
## Design choices

    - arXiv API over scraping. Free, official, no auth. Scraping breaks and is rude.

    - SQLite over vector DB for memory. Phase 1 does not need semantic search. SQLite is simpler.

    - Rate limiting from day one.

## Phases

    1. Agent core (current)
    
    2. Evals, safety, observability

    3. Cost, routing, reliability

    4. Deploy and ops

    5. Present

## License

MIT

```text

Also create `.env.example`:
```

```bash
GROQ_API_KEY=your_key_here
```