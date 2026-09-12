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

When the SMTP probe fails an address outright (-1), that's a spent lead —
falls back to one Apollo credit (verify_with_provider) to try to find a
correct email for that same person before giving up on them entirely.
"""
import smtplib
import socket

import dns.resolver

from db.db import get_conn
from pipeline.contacts import verify_with_provider

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


def verify_pending_contacts(contact_ids=None, limit=200):
    """
    By default scans up to `limit` globally-pending contacts (slow — each
    live SMTP probe can take several seconds, worse when a server blocks
    the probe outright). Pass `contact_ids` to scope this to a specific
    small set instead (e.g. only the contacts behind a send queue) so a
    single paced_send run doesn't stall scanning contacts unrelated to it.
    """
    conn = get_conn()
    try:
        if contact_ids:
            placeholders = ",".join("?" * len(contact_ids))
            rows = conn.execute(
                f"SELECT id, email FROM contacts "
                f"WHERE email_verified = 0 AND email IS NOT NULL AND id IN ({placeholders})",
                contact_ids,
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, email FROM contacts WHERE email_verified = 0 AND email IS NOT NULL LIMIT ?",
                (limit,),
            ).fetchall()

        checked = passed = failed = recovered = 0
        for row in rows:
            result = verify_smtp(row["email"])
            if result is True:
                conn.execute("UPDATE contacts SET email_verified = 1 WHERE id = ?", (row["id"],))
                passed += 1
            elif result is False:
                conn.execute("UPDATE contacts SET email_verified = -1 WHERE id = ?", (row["id"],))
                failed += 1
                conn.commit()
                try:
                    verify_with_provider(row["id"])  # spends 1 Apollo credit, may fix email+email_verified
                    still_bad = conn.execute(
                        "SELECT email_verified FROM contacts WHERE id = ?", (row["id"],)
                    ).fetchone()["email_verified"]
                    if still_bad == 1:
                        recovered += 1
                except Exception as e:
                    print(f"  Apollo fallback failed for contact {row['id']}: {e!r}")
            checked += 1
            conn.commit()
        print(f"Checked {checked}: {passed} passed, {failed} failed "
              f"({recovered} recovered via Apollo), "
              f"{checked - passed - failed} inconclusive (left pending).")
    finally:
        conn.close()


if __name__ == "__main__":
    verify_pending_contacts()
