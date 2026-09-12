"""
Polls sent threads for replies. Run periodically — cron, or by hand.
Uses the readonly scope already requested in gmail_client.py.

A thread with more than one message isn't necessarily a reply — a delayed
bounce notification (from mailer-daemon) also lands in the same thread and
was previously miscounted as one. This checks the actual sender of the
extra message(s): a genuine reply gets status='replied', a bounce that
slipped past the original send-time check gets corrected to 'bounced'
instead of being left incorrectly as 'sent' forever.
"""
import time

from db.db import get_conn
from sender.gmail_client import get_service


def check_replies():
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT id, gmail_thread_id FROM generated_emails "
            "WHERE status = 'sent' AND gmail_thread_id IS NOT NULL"
        ).fetchall()
        if not rows:
            return

        service = get_service()
        for row in rows:
            thread = service.users().threads().get(
                userId="me", id=row["gmail_thread_id"]
            ).execute()
            messages = thread.get("messages", [])
            if len(messages) <= 1:
                time.sleep(0.5)
                continue

            new_status = None
            for m in messages[1:]:
                msg = service.users().messages().get(
                    userId="me", id=m["id"], format="metadata", metadataHeaders=["From"]
                ).execute()
                headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
                sender = headers.get("From", "").lower()
                if "mailer-daemon" in sender:
                    new_status = new_status or "bounced"
                else:
                    new_status = "replied"
                    break  # a genuine reply takes priority over a bounce in the same thread

            if new_status:
                conn.execute(
                    "UPDATE generated_emails SET status = ? WHERE id = ?",
                    (new_status, row["id"]),
                )
                conn.commit()
            time.sleep(0.5)  # stay under Gmail's per-minute API quota
    finally:
        conn.close()


if __name__ == "__main__":
    check_replies()
