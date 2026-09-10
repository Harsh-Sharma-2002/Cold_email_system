#!/bin/bash
# Cron entry point for reply polling.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs
{
    echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
    .venv/bin/python -m sender.reply_tracker
} >> logs/reply_tracker.log 2>&1
