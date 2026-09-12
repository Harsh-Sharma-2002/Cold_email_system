# Nightly Agent Memory

Read this file at the start of every run. Append a new dated entry at the
end after each run (most recent last). Keep entries short: what happened,
any problems, anything the next run should know or watch for.

Do not delete history. If this file gets long, that's fine.

## Standing notes (update in place, not as dated entries)

- Apollo key status: fine as of 2026-09-11. User said they'll swap in a new
  key via `providers.enrichment.add_key()` when the current one runs out
  don't stop the whole run over one exhausted key, just note it here and
  move on to whatever doesn't need Apollo (or stop cleanly if nothing does).
- **Gmail account status: CONFIRMED past normal rate-limit range, likely a
  spam/abuse flag rather than a routine quota reset. Do not keep silently
  retrying — this needs the user to actually check their account.**
  Tested four times with a single resend to Sierra (generated_emails id 17):
    - 2026-09-11T02:19Z (~1-1.5h after the burst): "reached a limit" bounce
    - 2026-09-11T04:23Z (~3-3.5h after): "reached a limit" bounce
    - 2026-09-11T21:41Z (~20h after): "reached a limit" bounce
    - 2026-09-12T01:45Z (~24h after, past the researched 1-24h window):
      **bounced with "Message blocked" / "Message rejected" instead** —
      a different, more serious bounce type than the previous three (this
      is the same category as the 9 outright-blocked messages from the
      original burst, not the simple rate-limit message). A normal
      rate-limit block should have cleared by 24h; this one changed
      character instead of clearing, which points to spam/abuse flagging
      on the account, not just a quota window.
  Do NOT keep auto-retrying this on a timer expecting it to self-resolve.
  Tell the user directly: check https://myaccount.google.com/security and
  the Gmail inbox itself for any suspicious-activity notice from Google,
  since that's the more likely explanation now. Only resume sending once
  the user confirms the account looks normal, and even then start with a
  single test send, not a batch.
  **UPDATE 2026-09-12T03:23Z: a 5th test send to the same Sierra contact
  CLEARED — no bounce after 2+ minutes of waiting (every prior bounce in
  this saga arrived within 10-20s, so that's a reliable signal). Confirmed
  delivered, real Gmail message id 1a093a43194f2030, generated_emails id
  17 status='sent'. The account appears to be working again as of this
  timestamp. Still resume the rest of the 24 remaining bounced emails
  WITH PACING (sender/paced_send.py, 5 min apart, stops itself after 2
  consecutive bounces) rather than assuming it's fully healed and bursting
  again — that's exactly the mistake that caused this whole saga.**
- **CRITICAL — real sending limit for this account is MUCH lower than the
  20/night originally agreed, and sends must be paced, not fired in a
  burst.** Sending ~40 emails back to back from a personal Gmail account
  in under an hour got 25 of them bounced: 16 hit Gmail's own "you have
  reached a limit for sending mail" outbound rate limit, and 9 got
  outright blocked/rejected by Google's own mail infrastructure
  (mailer-daemon@googlemail.com) — spam/abuse detection on a personal
  account with no sending history suddenly firing many similar
  unsolicited emails.

  Researched actual numbers (2026): Gmail's hard technical cap is 500/day
  for a free account on a rolling 24-hour window (not midnight reset), but
  that's irrelevant here. For **unsolicited cold email from an unwarmed
  personal account**, the real safe ceiling is far lower:
    - New/unwarmed account: start at **10-20 emails/day**
    - Warm-up period: 2-4 weeks, roughly doubling weekly
    - Even established accounts: cap around 25-50/day; hourly throttling
      kicks in around ~20/hour regardless of daily total
    - If blocked: 1-24 hours before it clears; repeat violations make it
      worse and can permanently damage the account's reputation

  **Nightly cap is now 15 companies/night, not 20**, and sends within a
  run must be spaced out (at least 30-60 seconds apart, ideally spread
  across the available window rather than fired in a tight loop) rather
  than blasted back to back. This account has zero warm-up history as of
  2026-09-11 given tonight's bounces, so err toward the lower end (10-15)
  for at least the first couple weeks of real automated runs, watching
  actual delivered-vs-bounced results each run before increasing.
  Don't just trust the Gmail API response (`send_email` returning a
  message id does NOT mean delivery succeeded, it can still bounce
  asynchronously). After sending a batch, search the inbox for bounces
  (`from:mailer-daemon`) before trusting that a batch actually delivered,
  and correct any `generated_emails.status='sent'` rows that actually
  bounced to `status='bounced'` so they aren't miscounted as delivered.

## Run log

- 2026-09-10/11 (manual, not this automation): attempted 41 sends across
  three manual batches before the nightly cron existed, but **only 16
  actually delivered** — see the sending-must-be-paced standing note
  above for why. Actually delivered (`status='sent'`): company 89
  (Honeycomb) plus companies 61-75 (OpenAI, Anthropic, Scale AI, xAI,
  Cohere, Mistral AI, Perplexity, Rippling, Figma, Notion, Plaid, Brex,
  Ramp, Vercel, Retool). Bounced (`status='bounced'`, DB corrected after
  the fact): companies 76-80 (Sierra, Glean, Harvey AI, Cognition Labs,
  Cursor — blocked by Google) and the entire second batch of 20 — 6, 9,
  10, 11, 14, 81, 82, 83, 85, 86, 87, 90, 91, 92, 93, 95, 97, 98, 99, 100
  (NVIDIA, IBM, Salesforce, Adobe, Cisco, Writer, LangChain, Temporal,
  Imbue, Arize AI, Braintrust, Chronosphere, Coralogix, Weights & Biases,
  Anyscale, Pinecone, Airbyte, dbt Labs, Redpanda, Emotiv — 4 blocked, 16
  hit the rate limit). Those 25 companies have a real verified contact and
  a written email sitting in `generated_emails` with `status='bounced'`,
  they just need re-sending once the account's sending situation is sorted
  out and with real pacing between sends. Don't regenerate the emails,
  just resend the same content. 84 (CrewAI), 94 (Modal Labs), and 96
  (LlamaIndex) got zero Apollo contacts and are still `status='new'`
  untouched, skip them or retry later, no point burning research credits
  again without a different contact-finding approach. 55 companies remain
  fully untouched at `status='new'` as of this entry, mostly the big-tech
  bucket (Amazon, Microsoft, Google, Meta, Apple, etc, ids 1-60 minus the
  few already picked off) plus a handful of leftover startups.

(No fully automated cron runs yet as of this entry. First scheduled fire:
2026-09-11 03:00 America/Phoenix, but the user hasn't validated the
headless `claude -p --dangerously-skip-permissions` invocation under
cron's stripped environment yet, so treat the first real run as
unverified until AGENT_MEMORY.md shows a genuine automated entry below
this line.)

- 2026-09-12: **Found and fixed a false-positive bug in `reply_tracker.py`.**
  It marked a row `status='replied'` whenever `len(thread['messages']) > 1`,
  without checking who sent the extra message. A delayed bounce
  notification (from `mailer-daemon@googlemail.com`) lands in the same
  Gmail thread as the original send, so it satisfied that check too. This
  had falsely marked Chronosphere (id 33), Coralogix (id 34), and Weights
  & Biases (id 35) as `replied`, and Anyscale (id 36) and Pinecone (id 37)
  as `sent`, when a precise per-thread audit (checking the `From` header
  of every message past the first) showed all 5 actually bounced with
  "Message blocked" / "Message rejected" from Google — same block type as
  the original burst, not a new address problem. **There were 0 real
  replies, not 3.** Corrected all 5 rows back to `status='bounced'` in the
  DB. Fixed `reply_tracker.py` to check the `From` header and only count a
  message as a reply if it's not from `mailer-daemon`; if the only extra
  message(s) in a thread are bounces, it now sets `status='bounced'`
  instead of leaving the row stuck at `sent`.
  Also fixed the same blind spot in `paced_send.py`: its in-run bounce
  check only waited 25s after each batch of 5, which is too short — these
  5 bounces arrived later than that window and were missed at send time.
  Increased the wait to 60s as a faster circuit-breaker, but more
  importantly, `paced_send.run()` now calls `reply_tracker.check_replies()`
  as an authoritative final sweep after the whole run finishes, since that
  checks the actual thread content rather than a time-boxed search and
  will catch bounces that arrive after the in-run window regardless of
  delay.
  **Lesson for future runs: never trust a `sent`/`replied` count in this DB
  without having run `reply_tracker.check_replies()` (or the SessionStart
  hook, which calls it) first — the paced sender's own bounce check is
  only a fast circuit-breaker, not the source of truth.** Corrected totals
  as of this entry: 32 `sent` (verified via the fixed tracker), 9
  `bounced`, 27 `approved`/queued, 0 `replied`.
