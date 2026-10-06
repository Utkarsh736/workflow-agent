# Streaming note

## The bug

`chat_stream` prints tokens to stdout as they arrive.
It also returns the full text.

`run_test.py` printed the returned text again.
So the summary appeared twice.

## The lesson

A function that both prints and returns is easy to misuse.
The caller cannot know that the print already happened.

## The fix

For now: only `chat_stream` prints. The caller does not.

## A cleaner design (later)

`chat_stream(..., on_token=callback)`.
The tool never prints. The caller decides.
