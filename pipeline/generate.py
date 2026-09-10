"""
Stage 4: Generate. contact + research + resume + template -> email draft.
Never starts from a blank page — always template-guided.
"""
import json
from db.db import get_conn
from providers.llm import chat

with open("templates/email_template.txt") as f:
    TEMPLATE = f.read()

with open("resume.txt") as f:
    RESUME = f.read()

GENERATE_PROMPT = """You're writing a short, genuine cold email from a college
student to a recruiter/engineer, based on the template and research below.
Fill in the template's placeholders naturally — don't invent facts that
aren't present in the research. Keep it under 150 words. Return JSON:
{{"subject": "...", "body": "..."}}

TEMPLATE:
{template}

CANDIDATE BACKGROUND:
{resume}

CONTACT: {contact_name}, {contact_title}

RESEARCH:
{research}
"""


def generate_email(company_id: int, contact_id: int):
    conn = get_conn()
    try:
        contact = conn.execute("SELECT * FROM contacts WHERE id = ?", (contact_id,)).fetchone()
        research = conn.execute(
            "SELECT * FROM research WHERE company_id = ?", (company_id,)
        ).fetchone()
        research_text = json.dumps(dict(research), indent=2) if research else "(none yet)"

        prompt = GENERATE_PROMPT.format(
            template=TEMPLATE,
            resume=RESUME,
            contact_name=contact["name"],
            contact_title=contact["title"],
            research=research_text,
        )
        result = json.loads(chat([{"role": "user", "content": prompt}]))

        conn.execute(
            """
            INSERT INTO generated_emails (company_id, contact_id, subject, body, status)
            VALUES (?, ?, ?, ?, 'generated')
            """,
            (company_id, contact_id, result["subject"], result["body"]),
        )
        conn.execute(
            "UPDATE companies SET status = 'email_generated' WHERE id = ?", (company_id,)
        )
        conn.commit()
    finally:
        conn.close()
