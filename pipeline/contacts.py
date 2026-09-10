"""
Stage 3: Contact. Two ways to get a contact on the books:

- add_contact: you already have a name/title (team page, LinkedIn) —
  pattern-guesses an email for free.
- find_contacts: no name yet — searches Apollo's people-search endpoint
  (0 credits) for people at the domain matching SEARCH_TITLES. Returns
  candidates with first name + obfuscated last name + an Apollo person id;
  no email yet, since search doesn't reveal contact data.

Either way, verify_with_provider spends one Apollo credit via /people/match
to reveal the real email (and full name, for find_contacts candidates).
"""
import os
from db.db import get_conn
from providers import enrichment

COMMON_PATTERN = "{first}.{last}@{domain}"  # by far the most common at tech companies

# Titles to search for when no contact name is supplied. Comma-separated
# override via .env (APOLLO_SEARCH_TITLES).
DEFAULT_TITLES = [
    t.strip()
    for t in os.environ.get(
        "APOLLO_SEARCH_TITLES",
        "recruiter,technical recruiter,university recruiter,talent acquisition,engineering manager",
    ).split(",")
    if t.strip()
]

# How many find_contacts candidates per company get their email revealed
# (i.e. how many Apollo credits run_pipeline will spend per company).
MAX_VERIFY_PER_COMPANY = int(os.environ.get("MAX_VERIFY_PER_COMPANY", "1"))


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


def find_contacts(company_id: int, domain: str, titles: list[str] = None, max_results: int = 5):
    """Free (0-credit) Apollo people search — no name required. Finds
    candidates at `domain` matching `titles`, stores them with whatever
    Apollo's search hands back (first name, obfuscated last name, an
    external_id for later enrichment) and no email yet."""
    result = enrichment.request(
        "/mixed_people/api_search",
        method="POST",
        json={
            "q_organization_domains_list": [domain],
            "person_titles": titles or DEFAULT_TITLES,
            "per_page": max_results,
        },
    )
    people = result.get("people", [])
    if not people:
        return

    conn = get_conn()
    try:
        for p in people:
            name = f"{p.get('first_name', '')} {p.get('last_name_obfuscated', '')}".strip()
            conn.execute(
                """
                INSERT INTO contacts (company_id, name, title, source, external_id)
                VALUES (?, ?, ?, 'apollo_search', ?)
                """,
                (company_id, name, p.get("title"), p.get("id")),
            )
        conn.execute("UPDATE companies SET status = 'contact_found' WHERE id = ?", (company_id,))
        conn.commit()
    finally:
        conn.close()


def verify_with_provider(contact_id: int):
    """Spends one Apollo credit via /people/match with reveal_personal_emails
    (that flag is what actually triggers the charge) to reveal a real email.
    Matches by Apollo person id when find_contacts already resolved one
    (exact match, no guessing); falls back to name/domain otherwise."""
    conn = get_conn()
    try:
        contact = conn.execute(
            """
            SELECT ct.*, co.domain, co.name AS company_name
            FROM contacts ct JOIN companies co ON co.id = ct.company_id
            WHERE ct.id = ?
            """,
            (contact_id,),
        ).fetchone()
    finally:
        conn.close()

    payload = {"reveal_personal_emails": True}
    if contact["external_id"]:
        payload["id"] = contact["external_id"]
    else:
        parts = (contact["name"] or "").split()
        payload["first_name"] = parts[0] if parts else ""
        payload["last_name"] = parts[-1] if len(parts) > 1 else ""
        payload["domain"] = contact["domain"]
        payload["organization_name"] = contact["company_name"]

    result = enrichment.request("/people/match", method="POST", json=payload)
    person = result.get("person", {})
    email = person.get("email")
    if not email:
        return

    conn = get_conn()
    try:
        conn.execute(
            """
            UPDATE contacts
            SET email = ?, name = COALESCE(?, name), email_verified = 1,
                source = 'apollo', confidence = 1.0
            WHERE id = ?
            """,
            (email, person.get("name"), contact_id),
        )
        conn.commit()
    finally:
        conn.close()
