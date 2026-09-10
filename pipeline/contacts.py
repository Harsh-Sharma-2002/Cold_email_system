"""
Stage 3: Contact. Pattern-guess an email for free; optionally spend one
enrichment credit (Apollo/Hunter) to verify it when you actually want the
confidence bump.
"""
from db.db import get_conn
from providers import enrichment

COMMON_PATTERN = "{first}.{last}@{domain}"  # by far the most common at tech companies


def guess_email(first: str, last: str, domain: str, pattern: str = COMMON_PATTERN) -> str:
    # TODO: format pattern with first/last/f/l/domain, lowercased
    raise NotImplementedError


def add_contact(company_id: int, name: str, title: str, domain: str, linkedin: str = None):
    """You supply the name/title — from a team page, LinkedIn, wherever
    you're sourcing them. This just guesses the email and stores it."""
    # TODO: split name into first/last, guess_email, insert contacts row
    # TODO: mark company status='contact_found'
    raise NotImplementedError


def verify_with_provider(contact_id: int, first: str, last: str, domain: str, company_name: str):
    """Spends one Apollo credit via /people/match with reveal_personal_emails
    (that flag is what actually triggers the charge). Adjust the payload
    shape if ENRICHMENT_PROVIDER is set to something other than apollo."""
    # TODO: call enrichment.request("/people/match", ...), pull email out of response
    # TODO: update contacts row with verified email/source/confidence
    raise NotImplementedError
