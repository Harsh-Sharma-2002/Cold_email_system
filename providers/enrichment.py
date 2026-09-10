"""
Enrichment provider (contact-finding: Apollo, Hunter, or whatever's next).

Handles multiple API keys — free tier, then a trial, then another
account — burned through in order and persisted in SQLite, so it survives
across runs and never retries a key it already knows is dead.

Swapping vendors: change ENRICHMENT_BASE_URL / ENRICHMENT_AUTH_HEADER in
.env, and adjust the request path/payload where you call request() (see
pipeline/contacts.py). The key-rotation logic here doesn't change.

pip install requests python-dotenv
"""
import os
import requests
from dotenv import load_dotenv
from db.db import get_conn

load_dotenv()

BASE_URL = os.environ["ENRICHMENT_BASE_URL"]
AUTH_HEADER = os.environ.get("ENRICHMENT_AUTH_HEADER", "X-Api-Key")
PROVIDER = os.environ["ENRICHMENT_PROVIDER"]


def _ensure_seeded(conn):
    row = conn.execute("SELECT 1 FROM api_keys WHERE provider = ?", (PROVIDER,)).fetchone()
    if row is None and os.environ.get("ENRICHMENT_API_KEY"):
        conn.execute(
            "INSERT INTO api_keys (provider, key) VALUES (?, ?)",
            (PROVIDER, os.environ["ENRICHMENT_API_KEY"]),
        )
        conn.commit()


def add_key(key: str):
    """Call when you start the trial, or move to another account."""
    conn = get_conn()
    try:
        conn.execute("INSERT INTO api_keys (provider, key) VALUES (?, ?)", (PROVIDER, key))
        conn.commit()
    finally:
        conn.close()


def _active_key(conn):
    row = conn.execute(
        "SELECT id, key FROM api_keys WHERE provider = ? AND status = 'active' "
        "ORDER BY last_used ASC, id ASC LIMIT 1",
        (PROVIDER,),
    ).fetchone()
    if row is None:
        raise RuntimeError(f"No active {PROVIDER} API keys left — call add_key() to add one")
    return row["id"], row["key"]


def _mark_exhausted(conn, key_id):
    conn.execute("UPDATE api_keys SET status = 'exhausted' WHERE id = ?", (key_id,))
    conn.commit()


def _touch(conn, key_id):
    conn.execute("UPDATE api_keys SET last_used = CURRENT_TIMESTAMP WHERE id = ?", (key_id,))
    conn.commit()


def request(path: str, method: str = "GET", **kwargs):
    """Fires a request against the current provider, auto-rotating to the
    next stored key when this one reports it's out of credits, rate-limited,
    or invalid (401/402/403/429)."""
    conn = get_conn()
    try:
        _ensure_seeded(conn)
        base_headers = kwargs.pop("headers", {})
        while True:
            key_id, key = _active_key(conn)
            headers = {**base_headers, AUTH_HEADER: key}
            resp = requests.request(method, BASE_URL.rstrip("/") + path, headers=headers, **kwargs)
            if resp.status_code in (401, 402, 403, 429):
                _mark_exhausted(conn, key_id)
                continue
            resp.raise_for_status()
            _touch(conn, key_id)
            return resp.json()
    finally:
        conn.close()
