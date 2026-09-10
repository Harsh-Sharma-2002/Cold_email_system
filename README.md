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
2. `cp .env.example .env` and fill in: Tavily key, Groq or Ollama config, your
   first Apollo/Hunter key.
3. Write a few paragraphs of plain-text background into `resume.txt` — skills,
   projects, what you're looking for. The LLM reads this on every email it writes.
4. `python db/db.py` — creates `leads.db` from `schema.sql`.
5. Add companies to work through. Simplest way to start: open `leads.db` in any
   SQLite browser (e.g. DB Browser for SQLite) and add rows to `companies`
   (name, website) by hand or CSV import. A proper CSV-import script is a
   natural thing to add once the rest works end-to-end.
6. `python pipeline/run_pipeline.py` — runs research → extract → generate →
   critique over whatever's ready at each stage.
7. **Contacts**: the pipeline pattern-guesses an email once you give it a
   name/title (see `pipeline/contacts.py: add_contact`). Nothing here
   auto-discovers names yet — wire that up to however you're sourcing them
   (LinkedIn, a team page you read yourself, or `verify_with_provider` to
   spend an Apollo/Hunter credit).
8. `streamlit run dashboard/app.py` — review, edit, approve, or reject.
9. `python sender/send_approved.py` — sends only what you approved. Caps
   itself at `MAX_PER_RUN` per run; raise that slowly as your sending
   reputation builds.
10. `python sender/reply_tracker.py` — run this periodically (cron, or just
    by hand) to flag threads that got a reply.

## Adding an API key when one runs out

```python
from providers.enrichment import add_key
add_key("your_trial_or_next_account_key")
```

The next request automatically rotates to it — nothing else changes.
