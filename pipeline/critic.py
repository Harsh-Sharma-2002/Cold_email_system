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
    conn = get_conn()
    try:
        email = conn.execute(
            "SELECT * FROM generated_emails WHERE id = ?", (email_id,)
        ).fetchone()
        research = conn.execute(
            "SELECT * FROM research WHERE company_id = ?", (email["company_id"],)
        ).fetchone()
        research_text = json.dumps(dict(research), indent=2) if research else "(none yet)"

        prompt = CRITIC_PROMPT.format(
            research=research_text, subject=email["subject"], body=email["body"]
        )
        result = json.loads(chat_json([{"role": "user", "content": prompt}]))

        conn.execute(
            "UPDATE generated_emails SET critic_notes = ? WHERE id = ?",
            (json.dumps(result), email_id),
        )
        conn.commit()
    finally:
        conn.close()
