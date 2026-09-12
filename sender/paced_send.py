"""
Sends queued emails (status='bounced' or 'approved') one at a time, ~2
minutes apart (jittered — perfectly even intervals read as bot-like even
at low volume), checking for bounces every 5 sends rather than every
single one. Stops immediately the moment any bounce shows up in a batch
of 5, rather than working through the whole queue on a broken account.

Picks up 'bounced' rows first (already-written content, just re-sending)
then 'approved' rows, capped at MAX_PER_RUN.

Run once — it loops internally with the delay, no need for cron:
    python -m sender.paced_send
    python -m sender.paced_send --interval 120 --jitter 30 --batch 5 --max 50
"""
import argparse
import os
import random
import time
from datetime import datetime, timezone

from db.db import get_conn
from sender.gmail_client import send_email, get_service
from sender.reply_tracker import check_replies
from sender.verify_email import verify_pending_contacts
from sender.pacing_config import daily_cap, sending_window_open, sent_today_count

DEFAULT_INTERVAL_SECONDS = 120
DEFAULT_JITTER_SECONDS = 30
DEFAULT_BATCH_SIZE = 5
DEFAULT_MAX_PER_RUN = int(os.environ.get("MAX_PER_RUN", "50"))


def _candidate_contact_ids(conn, limit):
    """Contact ids behind the next `limit` bounced/approved rows, regardless
    of verification status — used to scope verify_pending_contacts to just
    this run instead of scanning every unverified contact in the DB."""
    rows = conn.execute(
        """
        SELECT ct.id
        FROM generated_emails ge
        JOIN contacts ct ON ct.id = ge.contact_id
        WHERE ge.status IN ('bounced', 'approved')
        ORDER BY CASE ge.status WHEN 'bounced' THEN 0 ELSE 1 END, ge.id
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [r["id"] for r in rows]


def _queued(conn, limit):
    return conn.execute(
        """
        SELECT ge.id, ge.subject, ge.body, ct.email, co.name AS company_name
        FROM generated_emails ge
        JOIN contacts ct ON ct.id = ge.contact_id
        JOIN companies co ON co.id = ge.company_id
        WHERE ge.status IN ('bounced', 'approved')
          AND ct.email_verified != -1
        ORDER BY CASE ge.status WHEN 'bounced' THEN 0 ELSE 1 END, ge.id
        LIMIT ?
        """,
        (limit,),
    ).fetchall()


def _bounced_since(service, subject, since_utc):
    safe_subject = subject.replace('"', '')
    results = service.users().messages().list(
        userId="me", q=f'from:mailer-daemon subject:"{safe_subject}"', maxResults=5
    ).execute()
    for m in results.get("messages", []):
        msg = service.users().messages().get(userId="me", id=m["id"], format="minimal").execute()
        ts = datetime.fromtimestamp(int(msg["internalDate"]) / 1000, tz=timezone.utc)
        if ts >= since_utc:
            return True
    return False


def run(interval_seconds, jitter_seconds, batch_size, max_per_run, ignore_window=False):
    if not ignore_window and not sending_window_open():
        print("Outside the weekday 8am-6pm sending window (America/Phoenix). Not sending. "
              "(pass --ignore-window to override)")
        return
    if ignore_window and not sending_window_open():
        print("Sending window check overridden by --ignore-window.")

    conn = get_conn()
    remaining_today = daily_cap() - sent_today_count(conn)
    if remaining_today <= 0:
        print(f"Daily cap ({daily_cap()}/day) already reached for today. Not sending.")
        conn.close()
        return
    effective_max = min(max_per_run, remaining_today)

    pool_size = max(effective_max * 3, 20)
    candidate_ids = _candidate_contact_ids(conn, pool_size)
    print(f"Verifying up to {len(candidate_ids)} contact address(es) behind the next "
          f"{pool_size} queued rows (MX + SMTP probe, Apollo fallback on failure)...")
    verify_pending_contacts(contact_ids=candidate_ids)

    queue = _queued(conn, effective_max)
    conn.close()

    if not queue:
        print("Nothing queued (no rows with status='bounced' or 'approved' and a verified address).")
        return

    print(f"{len(queue)} emails queued (daily cap {daily_cap()}, {remaining_today} left today). "
          f"~{interval_seconds}s +/-{jitter_seconds}s between sends, checking for bounces every {batch_size}.")
    service = get_service()

    sent_count = 0
    for batch_start in range(0, len(queue), batch_size):
        if not ignore_window and not sending_window_open():
            print("Sending window closed mid-run (past 6pm or into the weekend). Stopping here.")
            break
        batch = queue[batch_start:batch_start + batch_size]
        batch_sent_at = []

        for i, row in enumerate(batch):
            conn = get_conn()
            try:
                sent_at = datetime.now(timezone.utc)
                result = send_email(row["email"], row["subject"], row["body"])
                conn.execute(
                    "UPDATE generated_emails SET status='sent', sent_at=CURRENT_TIMESTAMP, "
                    "gmail_message_id=?, gmail_thread_id=? WHERE id=?",
                    (result.get("id"), result.get("threadId"), row["id"]),
                )
                conn.commit()
                batch_sent_at.append((row, sent_at))
                print(f"  sent -> {row['company_name']} ({row['email']})")
            except Exception as e:
                print(f"  ERROR sending to {row['company_name']}: {e!r}")
            conn.close()

            is_last_in_queue = (batch_start + i + 1) == len(queue)
            if not is_last_in_queue:
                delay = interval_seconds + random.uniform(-jitter_seconds, jitter_seconds)
                time.sleep(max(delay, 10))

        # Batch checkpoint: verify all sends in this batch of 5 before continuing.
        # This is only a fast circuit-breaker to stop a broken run early — some
        # bounces (Message rejected) arrive well after this window, so it can
        # miss real bounces. check_replies() below is the authoritative pass
        # that catches those later, using the thread itself rather than a
        # time-boxed search.
        print(f"  -- checking last {len(batch_sent_at)} sends for bounces --")
        time.sleep(60)  # give bounces time to arrive
        any_bounced = False
        for row, sent_at in batch_sent_at:
            if _bounced_since(service, row["subject"], sent_at):
                print(f"  BOUNCED -> {row['company_name']}")
                conn = get_conn()
                conn.execute("UPDATE generated_emails SET status='bounced' WHERE id=?", (row["id"],))
                conn.commit()
                conn.close()
                any_bounced = True
            else:
                sent_count += 1

        if any_bounced:
            print("Bounce detected in this batch of 5 — stopping the run now.")
            break

    print("Running a final authoritative bounce/reply sweep over all sent threads...")
    check_replies()
    conn = get_conn()
    still_sent = conn.execute(
        "SELECT COUNT(*) AS c FROM generated_emails WHERE id IN ({}) AND status='sent'".format(
            ",".join("?" * len(queue))
        ),
        [row["id"] for row in queue],
    ).fetchone()["c"]
    conn.close()
    print(f"\nDone. {sent_count} confirmed delivered this run "
          f"({still_sent} still marked 'sent' after the final sweep).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL_SECONDS,
                         help="base seconds between sends (default 120 = 2 min)")
    parser.add_argument("--jitter", type=int, default=DEFAULT_JITTER_SECONDS,
                         help="+/- random seconds added to interval (default 30)")
    parser.add_argument("--batch", type=int, default=DEFAULT_BATCH_SIZE,
                         help="check for bounces every N sends (default 5)")
    parser.add_argument("--max", type=int, default=DEFAULT_MAX_PER_RUN,
                         help="max emails this run (default 50)")
    parser.add_argument("--ignore-window", action="store_true",
                         help="bypass the weekday 8am-6pm sending-window check")
    args = parser.parse_args()
    run(args.interval, args.jitter, args.batch, args.max, ignore_window=args.ignore_window)
