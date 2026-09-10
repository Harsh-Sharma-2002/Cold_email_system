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
    # TODO: seed api_keys from ENRICHMENT_API_KEY if none stored yet for PROVIDER
    raise NotImplementedError


def add_key(key: str):
    """Call when you start the trial, or move to another account."""
    # TODO: insert a new active key row for PROVIDER
    raise NotImplementedError


def _active_key(conn):
    # TODO: return (id, key) for the oldest-used active key, or raise if none left
    raise NotImplementedError


def _mark_exhausted(conn, key_id):
    # TODO: flip status to 'exhausted'
    raise NotImplementedError


def _touch(conn, key_id):
    # TODO: bump last_used
    raise NotImplementedError


def request(path: str, method: str = "GET", **kwargs):
    """Fires a request against the current provider, auto-rotating to the
    next stored key when this one reports it's out of credits, rate-limited,
    or invalid (401/402/403/429)."""
    # TODO: loop over _active_key, fire request, rotate key on 401/402/403/429,
    # otherwise _touch and return resp.json()
    raise NotImplementedError
