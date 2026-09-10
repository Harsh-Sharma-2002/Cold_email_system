"""
Polls sent threads for replies. Run periodically — cron, or by hand.
Uses the readonly scope already requested in gmail_client.py.
"""
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
            if len(thread.get("messages", [])) > 1:
                conn.execute(
                    "UPDATE generated_emails SET status = 'replied' WHERE id = ?",
                    (row["id"],),
                )
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    check_replies()
