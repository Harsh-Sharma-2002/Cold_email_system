#!/bin/bash
# Cron entry point for the research -> extract -> find contacts -> verify ->
# generate -> critique loop. Never sends anything.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs
{
    echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
    .venv/bin/python -m pipeline.run_pipeline
} >> logs/run_pipeline.log 2>&1
