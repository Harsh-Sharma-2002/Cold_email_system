"""
Sends only what a human approved. Run manually — no cron, no auto-send.
Paces sends to protect your Gmail reputation; raise MAX_PER_RUN slowly.
"""
import os
from db.db import get_conn
from sender.gmail_client import send_email

MAX_PER_RUN = 20


def send_approved():
    max_per_run = int(os.environ.get("MAX_PER_RUN", MAX_PER_RUN))

    conn = get_conn()
    try:
        rows = conn.execute(
            """
            SELECT ge.id, ge.subject, ge.body, ct.email
            FROM generated_emails ge
            JOIN contacts ct ON ct.id = ge.contact_id
            WHERE ge.status = 'approved'
            LIMIT ?
            """,
            (max_per_run,),
        ).fetchall()

        for row in rows:
            result = send_email(row["email"], row["subject"], row["body"])
            conn.execute(
                """
                UPDATE generated_emails
                SET status = 'sent', sent_at = CURRENT_TIMESTAMP,
                    gmail_message_id = ?, gmail_thread_id = ?
                WHERE id = ?
                """,
                (result.get("id"), result.get("threadId"), row["id"]),
            )
            conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    send_approved()
