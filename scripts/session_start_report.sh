#!/bin/bash
# SessionStart hook: checks for new replies (touches Gmail), then reports
# current sending health so Claude and the user see it at the start of
# every session in this project, building a running picture of the
# sent/bounced/reply pattern over time.
set -uo pipefail
cd "$(dirname "$0")/.."

# Refresh reply status against Gmail (best-effort — don't fail the hook if
# this errors, e.g. token expired, no network).
.venv/bin/python -m sender.reply_tracker >/dev/null 2>&1 || true

STATS=$(.venv/bin/python -c "
import sqlite3, os
db_path = os.environ.get('DB_PATH', './leads.db')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
rows = conn.execute('SELECT status, COUNT(*) AS c FROM generated_emails GROUP BY status').fetchall()
counts = {r['status']: r['c'] for r in rows}
sent = counts.get('sent', 0)
replied = counts.get('replied', 0)
bounced = counts.get('bounced', 0)
approved = counts.get('approved', 0)
total_delivered = sent + replied
reply_rate = (replied / total_delivered * 100) if total_delivered else 0.0
print(f'{sent}|{replied}|{bounced}|{approved}|{reply_rate:.1f}')
" 2>/dev/null || echo "0|0|0|0|0.0")

IFS='|' read -r SENT REPLIED BOUNCED APPROVED REPLY_RATE <<< "$STATS"

SUMMARY="Cold email status: ${SENT} sent, ${REPLIED} replied (${REPLY_RATE}% reply rate), ${BOUNCED} queued as bounced, ${APPROVED} approved and not yet sent."

python3 -c "
import json
summary = '''$SUMMARY'''
print(json.dumps({
    'systemMessage': summary,
    'hookSpecificOutput': {
        'hookEventName': 'SessionStart',
        'additionalContext': summary,
    },
}))
"
