# workflow-agent

An AI agent that automates a boring, painful workflow.

This is a learning project for AI engineering.
The goal is to build one agent and add one production layer at a time.

Current status: **Phase 1 complete.**

## What it does

Every day, you want to know what is new on arXiv in AI.
The agent:
1. Searches arXiv for topics you care about.
2. Filters out papers it has shown you before.
3. Summarizes each new paper in 2–3 bullets.
4. Writes a Markdown digest file.

You talk to the agent in plain English.
The agent decides which tools to call.

## Quick start

```bash
uv sync
cp .env.example .env
# Add your GROQ_API_KEY to .env
uv run run_agent.py "Find new papers on 'agents' and 'evals'. Save a digest."
```

Open the digest:

```bash
cat digest/$(date +%F).md
```

## Architecture

```
User message
    ↓
Agent loop (agent/loop.py)
    ↓
Groq decides which tools to call
    ↓
┌──────────────────┬───────────────────┐
│ get_new_papers   │ save_digest       │
│ - arXiv search   │ - writes Markdown │
│ - filter seen    │ - reads run store │
│ - summarize      │                   │
│ - add to run     │                   │
└──────────────────┴───────────────────┘
    ↓
SQLite memory (data/memory.db)
    ↓
Digest file (digest/YYYY-MM-DD.md)
```

## Tools the agent can call

| Tool | What it does |
|---|---|
| `get_new_papers(topic, max_results)` | Search arXiv, filter seen, summarize, add to run |
| `save_digest()` | Write a Markdown digest for the current run |

## Design choices

### arXiv API over scraping
The API is free, official, and needs no auth.
Scraping breaks when the site changes.

### SQLite over a vector database for memory
Phase 1 only needs "have I seen this paper ID before?"
That is a lookup, not a semantic search.
SQLite is simpler and has no extra dependencies.

### Groq with `qwen/qwen3.8-27b`
Groq supports tool calling. Gemini does not.
The model is small, fast, and non-reasoning.
Summarization does not need a reasoning model.

### Run-scoped store instead of session handles
See `notes/session-design.md`.
This is a design lesson worth reading.

### Streaming summarizer
The summarizer prints tokens as they arrive.
The agent feels alive. The demo is convincing.
See `notes/streaming.md`.

### Rate limiting from day one
arXiv allows 1 request every 3 seconds.
Groq has per-minute limits.
Both are respected in code.

## Known limitations

- **Query precision is low.** `cat:cs.AI AND quantization` matches papers
  that mention quantization once. Phase 2 will improve this.
- **Memory is process-local.** The run-scoped store is lost on restart.
  Phase 3 will persist it.
- **No evals yet.** Phase 2 will add a golden test set.
- **No cost tracking yet.** Phase 3 will add budgets.

## Project structure

```
workflow-agent/
├── agent/
│   ├── config.py        # config + CLI override
│   ├── llm.py           # Groq client (chat and chat_stream)
│   ├── loop.py          # the agent loop
│   ├── memory.py        # SQLite seen-paper store
│   ├── prompts.py       # prompt templates
│   ├── sessions.py      # run-scoped paper store
│   ├── tool_schemas.py  # JSON schemas for tool calling
│   └── tools.py         # all tools
├── digest/              # output files
├── notes/               # design writeups
├── tests/
├── config.yaml
├── run_agent.py         # main entry point
└── run_test.py          # direct tool test (no agent loop)
```

## Phases

1. **Agent core** — current, complete.
2. Evals, safety, observability.
3. Cost, routing, reliability.
4. Deploy and ops.
5. Present.

## License

MIT