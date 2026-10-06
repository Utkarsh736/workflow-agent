# Tool calling note

## How the loop works

1. Send the model a list of tools. Each tool has a name,
   a description, and a JSON schema of inputs.
2. Send a user message.
3. The model replies. It answers, or it asks to call a tool.
4. Run the tool. Send the result back to the model.
5. Repeat until the model returns no tool calls,
   or we hit the max-turn limit (10).

## Design choices

### Max 10 turns
Safety limit. Phase 1 tasks are short. 10 is enough.
Without a limit, a confused model loops forever.
It burns tokens and never returns.

### Errors are returned to the model, not raised
When a tool fails, we send the error back as the tool result.
The model decides what to do.
In one run, both `get_new_papers` calls failed with a NameError.
The model reported the failure and stopped.
It did not hallucinate paper titles.
That is the behavior we want.

### Session handles vs run-scoped store
See `session-design.md`.

### Two tools, not five
The agent decides *which topics* to search and *whether to save*.
It does not manage SQLite or Markdown details.
Those are deterministic code.

This is a real design lesson:
**expose decisions, hide mechanics.**
