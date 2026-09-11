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
- Gmail rate limit status: tested twice with a single resend to Sierra
  (generated_emails id 17), both still bounced with "you have reached a
  limit for sending mail":
    - 2026-09-11T02:19Z (~1-1.5h after the original burst): still blocked
    - 2026-09-11T04:23Z (~3-3.5h after the original burst): still blocked
  Don't assume it's clear without testing. Before any future batch, send
  ONE email first, wait ~10s, search `from:mailer-daemon` for a fresh
  bounce with that exact subject, and only proceed with the rest of the
  batch if that one actually cleared. Researched guidance says blocks
  last 1-24h; given it's still blocked at 3.5h, expect it may take most
  of a full 24h window from the original burst (~2026-09-11 01:00-02:00Z)
  before this account can send again. If a future test around or after
  2026-09-12 01:00-02:00Z still bounces, that's past the researched
  1-24h range and worth flagging to the user as possibly a longer or
  different kind of restriction, not just normal rate-limit cooldown.
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
