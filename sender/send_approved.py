"""
Sends only what a human approved. Run manually — no cron, no auto-send.
Paces sends to protect your Gmail reputation; raise MAX_PER_RUN slowly.
"""
from db.db import get_conn
from sender.gmail_client import send_email

MAX_PER_RUN = 20


def send_approved():
    # TODO: select up to MAX_PER_RUN generated_emails with status='approved'
    # TODO: send_email for each, update status='sent', sent_at, gmail_message_id/thread_id
    raise NotImplementedError


if __name__ == "__main__":
    send_approved()
