"""
Stage 2: Extract. evidence -> structured research row, via LLM.
"""
import json
from db.db import get_conn
from providers.llm import chat_json

EXTRACTION_PROMPT = """You are helping a college student prepare a personalized
cold email to a tech company. Given the raw evidence below, extract ONLY
information useful for recruiting outreach. Return a JSON object with keys:
tech_stack (list), recent_news (list), open_roles (list),
engineering_focus (string), personalization_hooks (list of short, specific
facts worth mentioning in an email). If evidence is thin, return short or
empty lists rather than guessing.

EVIDENCE:
{evidence}
"""


def extract_research(company_id: int):
    # TODO: load evidence rows for company_id; bail if none
    # TODO: combine evidence text (truncated), call chat_json with EXTRACTION_PROMPT
    # TODO: upsert into research table, mark company status='extracted'
    raise NotImplementedError
