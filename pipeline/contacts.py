"""
Stage 3: Contact. Pattern-guess an email for free; optionally spend one
enrichment credit (Apollo/Hunter) to verify it when you actually want the
confidence bump.
"""
from db.db import get_conn
from providers import enrichment

COMMON_PATTERN = "{first}.{last}@{domain}"  # by far the most common at tech companies


def guess_email(first: str, last: str, domain: str, pattern: str = COMMON_PATTERN) -> str:
    return pattern.format(
        first=first.lower(),
        last=last.lower(),
        f=first[0].lower(),
        l=last[0].lower(),
        domain=domain.lower(),
    )


def add_contact(company_id: int, name: str, title: str, domain: str, linkedin: str = None):
    """You supply the name/title — from a team page, LinkedIn, wherever
    you're sourcing them. This just guesses the email and stores it."""
    parts = name.split()
    first, last = parts[0], parts[-1] if len(parts) > 1 else ""
    email = guess_email(first, last, domain)

    conn = get_conn()
    try:
        conn.execute(
            """
            INSERT INTO contacts (company_id, name, title, linkedin, email, source, confidence)
            VALUES (?, ?, ?, ?, ?, 'pattern_guess', 0.5)
            """,
            (company_id, name, title, linkedin, email),
        )
        conn.execute("UPDATE companies SET status = 'contact_found' WHERE id = ?", (company_id,))
        conn.commit()
    finally:
        conn.close()


def verify_with_provider(contact_id: int, first: str, last: str, domain: str, company_name: str):
    """Spends one Apollo credit via /people/match with reveal_personal_emails
    (that flag is what actually triggers the charge). Adjust the payload
    shape if ENRICHMENT_PROVIDER is set to something other than apollo."""
    result = enrichment.request(
        "/people/match",
        method="POST",
        json={
            "first_name": first,
            "last_name": last,
            "domain": domain,
            "organization_name": company_name,
            "reveal_personal_emails": True,
        },
    )
    person = result.get("person", {})
    email = person.get("email")
    if not email:
        return

    conn = get_conn()
    try:
        conn.execute(
            "UPDATE contacts SET email = ?, email_verified = 1, source = 'apollo', confidence = 1.0 WHERE id = ?",
            (email, contact_id),
        )
        conn.commit()
    finally:
        conn.close()
