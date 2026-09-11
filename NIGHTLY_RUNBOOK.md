# Nightly Cold Email Runbook

You are running unattended, triggered by cron at 3 AM with
`--dangerously-skip-permissions`. Nobody is watching. Be careful, stay
inside this project directory (`~/Desktop/Work_Dir/cold_email`), and don't
touch anything outside the scope below.

Read `AGENT_MEMORY.md` first for context from previous runs. Update it at
the end of this run (append a dated entry; update the standing notes if
Apollo key status or the cap changed).

## Why you're doing this yourself instead of calling an LLM API

A local qwen3:8b model used to do extraction/generation/critique here. It
hallucinated (attributed a company's tech stack to the candidate as if it
were his own experience) and its own critique pass didn't catch it. You
replace all of that: you read the evidence and the resume yourself, you
write the email yourself, you critique it yourself. Don't delegate any of
this back to `providers.llm.chat` / `chat_json` — that path still exists in
the code but should not be used for anything user-facing here.

## Scope and caps

- Process **up to 15 companies** this run, no more (dropped from 20 after
  a 2026-09-11 incident, see below and `AGENT_MEMORY.md`). First, check
  `generated_emails` for any `status='bounced'` rows from a prior run —
  those already have a verified contact and a written email, just resend
  the same subject/body via `sender.gmail_client.send_email` again (don't
  regenerate), and they count toward this run's 15. Fill any remaining
  slots with companies at `status = 'new'`, ordered by `id`.
- **Sending must be paced, not fired in a burst — this is not optional.**
  A 2026-09-11 run that sent ~40 emails back to back in under an hour got
  25 of them bounced (16 hit Gmail's outbound rate limit, 9 got blocked by
  Google's spam/abuse detection on a personal account with no sending
  history). Wait **at least 30-60 seconds between each `send_email` call**,
  more if you have the time budget — spread across the run rather than
  looped tightly. A message id back from `send_email` does NOT mean it was
  delivered, Gmail can still bounce it asynchronously afterward.
- **After finishing all sends, search the inbox for bounces before closing
  out the run**: `service.users().messages().list(userId='me',
  q='from:mailer-daemon')` via `sender.gmail_client.get_service()`, for
  messages received in roughly the last hour. For anything that bounced,
  update that `generated_emails` row from `status='sent'` to
  `status='bounced'` so it isn't miscounted as delivered, and log it in
  `AGENT_MEMORY.md` so a future run resends it (see the cap note above).
- Spend **at most 1 Apollo reveal credit per company** (matches
  `MAX_VERIFY_PER_COMPANY` in `.env`) — free search first, one reveal only.
- If Apollo comes back exhausted/unauthorized (401/403) partway through,
  stop calling Apollo for the rest of the run, note it in
  `AGENT_MEMORY.md`, and still send what you can for companies whose
  contact was already verified before the failure. Don't error out the
  whole run over it.
- If Tavily errors out (quota/rate-limit), don't fail that company's
  research — use your own WebSearch tool for that company instead
  (`{company_name} engineering team tech stack recent news hiring`, or
  similar), then still scrape `PAGES_TO_TRY` paths off the website with
  `providers.scraper.fetch_page_text` as normal. Insert what you find into
  the `evidence` table the same way `pipeline/research.py` would
  (`source='search'` for the fallback web results), so the DB stays
  consistent for any future stage that reads from it.

## Per-company pipeline

For each company in this run's batch, in order:

1. **Research.** Call `pipeline.research.research_company(company_id, name,
   website)` (Tavily + site scraping, no LLM). If it raises on the Tavily
   call specifically, fall back per the Tavily note above rather than
   skipping the company entirely.

2. **Contacts.** Derive `domain` from `website` if `companies.domain` is
   empty (same logic as `pipeline/run_pipeline.py`:
   `_domain_from_website`), then call
   `pipeline.contacts.find_contacts(company_id, domain)` — a free (0-credit)
   Apollo search. From the candidates it inserts, prefer one whose title
   contains "talent" or "recruit" (case-insensitive) over an "Engineering
   Manager"; if none match, take the first. Call
   `pipeline.contacts.verify_with_provider(contact_id)` on that one pick to
   reveal a real email (1 credit). If it comes back with no email, try the
   next candidate for that company (still counts toward the 1-credit cap
   conceptually — don't try more than 2-3 candidates deep before giving up
   on that company and moving to the next).

3. **Read the evidence yourself.** Query the `evidence` table for this
   company (raw search + scraped page text). You are replacing
   `pipeline/extract.py`'s LLM call — read it directly, don't call
   `extract_research()`. Pull out 1-2 genuinely specific, verifiable facts
   (an actual blog post title, a direct quote, a specific hiring signal) —
   not vague summaries. If the evidence is thin or generic (common for
   giant multi-product companies), don't force a fake-specific hook; write
   a more general but still honest email instead.

4. **Write the email yourself.** Ground every claim about the *company* in
   the evidence you just read, and every claim about the *candidate* in
   `resume.txt` (read it fresh each run — the user may have updated it).
   Never attribute the company's tech stack, projects, or facts to the
   candidate, and never invent a candidate project/skill/metric that isn't
   literally in `resume.txt`. Use `templates/email_template.txt` as a loose
   structural guide, not a fill-in-the-blank form.

   Hard constraints on the writing itself:
   - **No em dashes (`—`) and no double hyphens (`--`) anywhere.** Use
     periods, commas, or "and" instead. This was an explicit correction
     from the user, check every draft for both before moving on.
   - Vary sentence structure and opening lines across the emails in this
     run. Don't reuse the same opening phrase or paragraph shape for every
     company. Read back over what you've written so far in this run before
     writing the next one if you're worried about repetition.
   - Keep it under ~150 words, one clear call to action, sign off "Harsh
     Sharma".
   - Sound like a person who actually read about the company, not a
     template. If you can't find something specific enough to say
     honestly, say less rather than padding with generic enthusiasm.

5. **Critique it yourself.** Before sending, re-read the draft against the
   evidence and `resume.txt` line by line. Check for: any claim not
   supported by either source, wrong company name, generic/templated
   phrasing, weak or missing call-to-action, and the em-dash/double-hyphen
   rule above. Fix issues yourself rather than sending something you know
   is off. Insert the result into `generated_emails` with `status =
   'approved'` and `critic_notes` summarizing what you checked (same shape
   as prior runs: `{"approved": true, "issues": [...], "reviewer": "claude
   (nightly automation)", "note": "..."}`).

6. **Send it, then wait.** Call `sender.gmail_client.send_email(contact_email,
   subject, body)`. It attaches `resume.pdf` automatically if present,
   nothing extra needed. Update the `generated_emails` row: `status='sent'`,
   `sent_at=CURRENT_TIMESTAMP`, `gmail_message_id`/`gmail_thread_id` from
   the result. Update `companies.status = 'email_generated'` (matches the
   convention the rest of the codebase uses; nothing currently sets
   `'sent'`/`'approved'` on the companies table itself, only on
   `generated_emails`). **Then sleep at least 30-60 seconds before moving to
   the next company** — see the pacing note under Scope and caps, this is
   the step it applies to.

7. Move to the next company. If something throws for one company (bad
   domain, no evidence found, no contact revealed), log it and continue,
   don't let one failure stop the batch.

## After the batch

**First, check for bounces** (see the bullet under Scope and caps) and
correct any `generated_emails` rows that actually bounced before you write
anything else down, otherwise the log below will report a delivery count
that isn't real.

Then append a dated entry to `AGENT_MEMORY.md`: how many companies you
processed, how many emails **actually delivered vs bounced** (not just how
many `send_email` calls you made), any companies you skipped and why, any
Apollo/Tavily issues hit, and anything unusual worth flagging to the user
in the morning. Keep it to a few lines, this is a log, not a report.
