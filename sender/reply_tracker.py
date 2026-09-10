"""
Polls sent threads for replies. Run periodically — cron, or by hand.
Uses the readonly scope already requested in gmail_client.py.
"""
from db.db import get_conn
from sender.gmail_client import get_service


def check_replies():
    # TODO: for each generated_emails row with status='sent', fetch its Gmail thread
    # TODO: if the thread has more than one message, mark status='replied'
    raise NotImplementedError


if __name__ == "__main__":
    check_replies()
