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
    # TODO: load contact + research, build GENERATE_PROMPT, call chat() for JSON
    # TODO: insert generated_emails row (status='generated'), mark company status='email_generated'
    raise NotImplementedError
