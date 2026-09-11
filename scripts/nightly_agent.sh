#!/bin/bash
# Cron entry point for the fully autonomous nightly batch: research, find
# contacts, write, critique, and send up to 20 emails, all done by a live
# Claude Code session (not the local qwen3:8b model) so quality matches
# what a human would write. See NIGHTLY_RUNBOOK.md for the actual process
# and AGENT_MEMORY.md for cross-run state.
#
# --dangerously-skip-permissions is required here: nobody is present at
# 3 AM to approve tool calls interactively.
set -uo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs
{
    echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
    /opt/homebrew/bin/claude -p "Read AGENT_MEMORY.md, then follow NIGHTLY_RUNBOOK.md exactly to run tonight's batch of up to 20 companies (research, find contacts, write, critique, and send each email yourself). Update AGENT_MEMORY.md with a dated entry when done." \
        --dangerously-skip-permissions
} >> logs/nightly_agent.log 2>&1
