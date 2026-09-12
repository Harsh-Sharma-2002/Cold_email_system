"""
Daily volume cap + sending-window rules, separate from the per-send
interval in paced_send.py. Established outreach platforms (Instantly,
Smartlead, etc.) treat total daily volume and business-hours-only
sending as bigger deliverability levers than inter-send spacing alone —
this is the "ramp" half of that: a new/aged-but-unused sending account
starts at a lower daily cap and steps up after a week, on weekdays only.

State (ramp start date) lives in sending_state.json, gitignored, next to
the DB — reset that file (or delete it) whenever a NEW sending account
is put into use, so the ramp restarts from day 1 for that account.
"""
import json
import os
from datetime import date, datetime
from zoneinfo import ZoneInfo

STATE_PATH = os.path.join(os.path.dirname(__file__), "..", "sending_state.json")
TIMEZONE = ZoneInfo("America/Phoenix")

RAMP_DAYS = 7
RAMP_DAILY_CAP = 20
POST_RAMP_DAILY_CAP = 30

WINDOW_START_HOUR = 8
WINDOW_END_HOUR = 18


def _load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH) as f:
            return json.load(f)
    state = {"ramp_start_date": date.today().isoformat()}
    with open(STATE_PATH, "w") as f:
        json.dump(state, f)
    return state


def daily_cap():
    state = _load_state()
    start = date.fromisoformat(state["ramp_start_date"])
    days_elapsed = (date.today() - start).days
    return RAMP_DAILY_CAP if days_elapsed < RAMP_DAYS else POST_RAMP_DAILY_CAP


def sending_window_open(now=None):
    now = now or datetime.now(TIMEZONE)
    if now.weekday() >= 5:  # Sat/Sun
        return False
    return WINDOW_START_HOUR <= now.hour < WINDOW_END_HOUR


def sent_today_count(conn):
    row = conn.execute(
        "SELECT COUNT(*) AS c FROM generated_emails "
        "WHERE status IN ('sent', 'replied') AND date(sent_at, 'localtime') = date('now', 'localtime')"
    ).fetchone()
    return row["c"]
