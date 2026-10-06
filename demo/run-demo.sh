#!/usr/bin/env bash
#
# Demo script for workflow-agent.
# Runs a full agent workflow with pauses for readability.
# Use with: asciinema rec demo.cast -c "bash demo/run-demo.sh"
#

set -e

# Helper: print a command, then run it, with a pause before.
run_step() {
    local cmd="$1"
    sleep 2
    echo "\$ $cmd"
    sleep 1
    eval "$cmd"
    echo
}

# Clear the screen for a clean start.
clear
sleep 2

# Optional: clean memory for a fresh demo.
# Comment this out if you want to preserve memory.
run_step "rm -f data/memory.db"

# Run the agent.
run_step "uv run run_agent.py \"Find new papers on 'mcp' and 'prompt injection'. Save a digest.\""

# Show the digest.
run_step "cat digest/\$(date +%F).md"

# Final pause so viewers can read the output.
sleep 3
