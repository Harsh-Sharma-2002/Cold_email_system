#!/bin/bash
# Cron entry point for sending. Only ever sends generated_emails rows
# already marked status='approved' in the dashboard — this never approves
# anything itself, it just delivers what a human already signed off on.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs
{
    echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
    .venv/bin/python -m sender.send_approved
} >> logs/send_approved.log 2>&1
