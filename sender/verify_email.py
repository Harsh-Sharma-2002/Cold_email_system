"""
Lightweight pre-send verification: MX lookup + SMTP RCPT TO probe, done
before spending a send on an address. Free, but not perfect — catch-all
domains accept any RCPT TO, so a pass here isn't a delivery guarantee,
only a filter against the clearly-broken addresses that cause hard
bounces (which are the ones that actually damage sender reputation).

contacts.email_verified semantics: 0 = not yet checked (default),
1 = passed (deliverable or at least accepted), -1 = failed (bad address,
skip it). An inconclusive probe (blocked/greylisted/timed out) leaves it
at 0 rather than guessing — never treat "couldn't confirm" as a fail.
"""
import smtplib
import socket

import dns.resolver

from db.db import get_conn

PROBE_FROM = "verify-probe@gmail.com"


def _mx_hosts(domain):
    try:
        answers = dns.resolver.resolve(domain, "MX", lifetime=8)
        return sorted((r.preference, str(r.exchange).rstrip(".")) for r in answers)
    except Exception:
        return []


def verify_smtp(email, timeout=8):
    """True = deliverable, False = bad address, None = inconclusive (don't block on this)."""
    if "@" not in email:
        return False
    domain = email.rsplit("@", 1)[1]
    hosts = _mx_hosts(domain)
    if not hosts:
        return False

    for _, host in hosts[:2]:
        try:
            with smtplib.SMTP(host, 25, timeout=timeout) as smtp:
                smtp.helo("gmail.com")
                smtp.mail(PROBE_FROM)
                code, _ = smtp.rcpt(email)
                if code == 250:
                    return True
                if code in (550, 551, 553):
                    return False
                return None  # ambiguous (450 greylist, 421, etc.)
        except (socket.timeout, smtplib.SMTPException, OSError):
            continue
    return None  # every MX host unreachable or blocked our probe


def verify_pending_contacts(limit=200):
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT id, email FROM contacts WHERE email_verified = 0 AND email IS NOT NULL LIMIT ?",
            (limit,),
        ).fetchall()
        checked = passed = failed = 0
        for row in rows:
            result = verify_smtp(row["email"])
            if result is True:
                conn.execute("UPDATE contacts SET email_verified = 1 WHERE id = ?", (row["id"],))
                passed += 1
            elif result is False:
                conn.execute("UPDATE contacts SET email_verified = -1 WHERE id = ?", (row["id"],))
                failed += 1
            checked += 1
            conn.commit()
        print(f"Checked {checked}: {passed} passed, {failed} failed, "
              f"{checked - passed - failed} inconclusive (left pending).")
    finally:
        conn.close()


if __name__ == "__main__":
    verify_pending_contacts()
