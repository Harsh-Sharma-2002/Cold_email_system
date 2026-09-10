# Cold Email Bot — Student Edition

Research once. Generate many. Send carefully. Every stage reads/writes
only the database — nothing calls another stage directly, so you can
re-run any single piece in isolation while you're building this.

## Status flow

```
new -> researched -> extracted -> contact_found -> email_generated -> approved -> sent -> replied
```

## Where each piece lives

```
db/          schema.sql + db.py            shared SQLite connection + schema
providers/   llm.py, enrichment.py,        swappable vendors — everything
             search.py, scraper.py         vendor-specific lives here, .env drives it
pipeline/    research / extract / contacts /   the actual stages, one file each,
             generate / critic / run_pipeline    matching Retrieve→Extract→Rank→
                                                  Generate→Critique
dashboard/   app.py                        Streamlit approval queue — nothing sends here
sender/      gmail_client.py,              Gmail send (human-approved only)
             send_approved.py,              + reply polling
             reply_tracker.py
templates/   email_template.txt            base structure the LLM fills in
resume.txt                                 plain-text background the LLM reads every time
```

## Setup

1. `pip install -r requirements.txt`
2. `cp .env.example .env` and fill in: Tavily key, your first Apollo/Hunter
   key. `LLM_BASE_URL`/`LLM_MODEL` default to a local Ollama running Qwen3
   8B (free, no key) — install Ollama, then `ollama pull qwen3:8b`. Swap to
   a hosted provider later by editing those three `LLM_*` vars — no code
   changes.
3. Write a few paragraphs of plain-text background into `resume.txt` — skills,
   projects, what you're looking for. The LLM reads this on every email it
   writes. Separately, drop an actual resume PDF at the path in
   `RESUME_ATTACHMENT_PATH` (defaults to `resume.pdf`) — it's attached to
   every email the sender sends, if present.
4. `python -m db.db` — creates `leads.db` from `schema.sql`.
5. Add companies to work through. Simplest way to start: open `leads.db` in any
   SQLite browser (e.g. DB Browser for SQLite) and add rows to `companies`
   (name, website) by hand or CSV import. A proper CSV-import script is a
   natural thing to add once the rest works end-to-end.
6. `python -m pipeline.run_pipeline` — runs research → extract → find
   contacts → verify → generate → critique over whatever's ready at each
   stage. (Run as a module, not `python pipeline/run_pipeline.py` — the
   `db`/`providers` imports need the project root on `sys.path`, which only
   `-m` guarantees.)
7. **Contacts** are now automatic: `find_contacts` does a free (0-credit)
   Apollo people-search per company against `APOLLO_SEARCH_TITLES`, then up
   to `MAX_VERIFY_PER_COMPANY` of those candidates get their email revealed
   via `verify_with_provider` (1 Apollo credit each — that cap is what
   bounds credit spend per company per run). You can still add a contact by
   hand with `pipeline/contacts.py: add_contact` if you already have a
   name/title from somewhere (LinkedIn, a team page).
8. `streamlit run dashboard/app.py` — review, edit, approve, or reject.
9. `python -m sender.send_approved` — sends only what you approved. Caps
   itself at `MAX_PER_RUN` per run; raise that slowly as your sending
   reputation builds.
10. `python -m sender.reply_tracker` — run this periodically (cron, or just
    by hand) to flag threads that got a reply.

## Running it unattended (cron)

`scripts/` holds thin wrappers cron can call directly — each `cd`s into the
project, uses `.venv/bin/python`, and appends to `logs/`:

```
scripts/run_pipeline.sh    research → extract → find contacts → verify → generate → critique
scripts/send_approved.sh   sends whatever you've already clicked Approve on
scripts/reply_tracker.sh   polls sent threads for replies
```

Install them with `crontab -e` (see `scripts/crontab.example` for the exact
lines this repo uses: pipeline every 6h, send every hour, replies daily).
Sending is still gated on your approval in the dashboard — cron only
delivers what's already marked `approved`, it never approves anything
itself.

## Adding an API key when one runs out

```python
from providers.enrichment import add_key
add_key("your_trial_or_next_account_key")
```

The next request automatically rotates to it — nothing else changes.
