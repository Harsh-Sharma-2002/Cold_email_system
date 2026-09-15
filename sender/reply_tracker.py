"""
Polls sent threads for replies. Run periodically — cron, or by hand.
Uses the readonly scope already requested in gmail_client.py.

A thread with more than one message isn't necessarily a reply — a delayed
bounce notification also lands in the same thread and was previously
miscounted as one. Checking only for "mailer-daemon" in the From header
(the first fix) still missed bounces from a recipient's own mail system
(e.g. systems-postmaster@world.deshaw.com), which don't contain that
string at all. The reliable signal is the MIME Content-Type: a bounce is
a standards-based Delivery Status Notification
(RFC 3464, `multipart/report; report-type=delivery-status`), regardless
of what the sending address happens to be called. That's the primary
check now; the From-header substring check is kept as a fallback for any
bounce that doesn't set the DSN content type correctly.

Checks both the active sending account and the retired one (if its
credentials/token backup still exists) — a row's thread lives in
whichever mailbox actually sent it, and we still want reply/bounce
visibility on everything already sent from the old account even though
it's no longer sending new mail.
"""
import os
import time

from googleapiclient.errors import HttpError

from db.db import get_conn
from sender.gmail_client import get_service

OLD_CREDS_PATH = "credentials_old_flagged_account.json"
OLD_TOKEN_PATH = "token_old_flagged_account.json"


def _fetch_thread(service, thread_id):
    try:
        return service.users().threads().get(userId="me", id=thread_id).execute()
    except HttpError as e:
        if e.resp.status == 404:
            return None
        raise


def check_replies():
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT id, contact_id, gmail_thread_id FROM generated_emails "
            "WHERE status = 'sent' AND gmail_thread_id IS NOT NULL"
        ).fetchall()
        if not rows:
            return

        service = get_service()
        old_service = None
        old_service_tried = False
        skipped = 0

        for row in rows:
            thread = _fetch_thread(service, row["gmail_thread_id"])
            active_service = service

            if thread is None:
                if not old_service_tried:
                    old_service_tried = True
                    if os.path.exists(OLD_TOKEN_PATH) and os.path.exists(OLD_CREDS_PATH):
                        old_service = get_service(OLD_CREDS_PATH, OLD_TOKEN_PATH)
                if old_service:
                    thread = _fetch_thread(old_service, row["gmail_thread_id"])
                    active_service = old_service

            if thread is None:
                skipped += 1
                time.sleep(0.5)
                continue

            messages = thread.get("messages", [])
            if len(messages) <= 1:
                time.sleep(0.5)
                continue

            new_status = None
            for m in messages[1:]:
                msg = active_service.users().messages().get(
                    userId="me", id=m["id"], format="metadata",
                    metadataHeaders=["From", "Content-Type"],
                ).execute()
                headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
                sender = headers.get("From", "").lower()
                content_type = headers.get("Content-Type", "").lower()
                is_bounce = (
                    "report-type=delivery-status" in content_type
                    or "mailer-daemon" in sender
                    or "postmaster" in sender
                )
                if is_bounce:
                    new_status = new_status or "bounced"
                else:
                    new_status = "replied"
                    break  # a genuine reply takes priority over a bounce in the same thread

            if new_status:
                conn.execute(
                    "UPDATE generated_emails SET status = ? WHERE id = ?",
                    (new_status, row["id"]),
                )
                if new_status == "bounced":
                    # A contact that already passed the pre-send SMTP probe
                    # (email_verified=1) never gets re-probed by
                    # verify_pending_contacts (it only rechecks
                    # email_verified=0), so a hard bounce here is the only
                    # signal that address is actually dead. Without this,
                    # the same dead address gets resent and re-bounces on
                    # every future paced_send run indefinitely, and each
                    # repeat trips the batch-of-5 circuit breaker.
                    conn.execute(
                        "UPDATE contacts SET email_verified = -1 WHERE id = ?",
                        (row["contact_id"],),
                    )
                conn.commit()
            time.sleep(0.5)  # stay under Gmail's per-minute API quota

        if skipped:
            print(f"Skipped {skipped} row(s) — thread not found in either the active or "
                  f"retired mailbox (likely deleted or a stale ID).")
    finally:
        conn.close()


if __name__ == "__main__":
    check_replies()
