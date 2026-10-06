# Session design note

## The problem

An agent that collects data across multiple tool calls
must share that data with a later tool call.

## The first attempt

We passed a `session_id` between tools.
`get_new_papers` created a new session each time.
`save_digest` used the last session_id.

## The failure

When the agent called `get_new_papers` twice,
two sessions were created.
`save_digest` saved only the last one.
Half the data was silently lost.

The agent reported success. The bug was invisible.

## The fix

Use a run-scoped store instead of explicit session handles.

- `get_new_papers` appends to the current run.
- `save_digest` reads the current run. It takes no arguments.
- The model cannot lose data. It has nothing to remember.

## The tradeoff

Less flexible. The agent cannot save two digests from one run.
For our workflow, that is fine.

## The lesson

Every piece of state the model must carry is a chance for it to fail.
Move state into the server when you can.
