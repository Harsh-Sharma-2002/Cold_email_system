"""
Stage 5: Critique. Second LLM pass — catches hallucinated claims, generic
phrasing, wrong company name, weak personalization, weak CTA. This is a
check for a human to read at approval time, not an auto-reject.
"""
import json
from db.db import get_conn
from providers.llm import chat_json

CRITIC_PROMPT = """Review this cold email a college student is about to send.
The research it's based on is included so you can catch hallucinated facts.
Return JSON: {{"approved": true/false, "issues": ["..."]}}. Flag: claims not
supported by the research, generic/templated-sounding phrasing, wrong
company name, weak or missing personalization, weak or missing call-to-action.

RESEARCH:
{research}

EMAIL SUBJECT: {subject}
EMAIL BODY:
{body}
"""


def critique_email(email_id: int):
    # TODO: load email + its company's research, build CRITIC_PROMPT, call chat_json
    # TODO: store parsed result JSON into generated_emails.critic_notes
    raise NotImplementedError
