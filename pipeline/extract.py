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
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT source, url, raw_content FROM evidence WHERE company_id = ?",
            (company_id,),
        ).fetchall()
        if not rows:
            return

        combined = "\n\n".join(
            f"[{r['source']}] {r['url']}\n{r['raw_content']}" for r in rows if r["raw_content"]
        )[:12000]

        prompt = EXTRACTION_PROMPT.format(evidence=combined)
        result = json.loads(chat_json([{"role": "user", "content": prompt}]))

        conn.execute(
            """
            INSERT INTO research (company_id, tech_stack, recent_news, open_roles,
                                   engineering_focus, personalization_hooks, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(company_id) DO UPDATE SET
                tech_stack=excluded.tech_stack,
                recent_news=excluded.recent_news,
                open_roles=excluded.open_roles,
                engineering_focus=excluded.engineering_focus,
                personalization_hooks=excluded.personalization_hooks,
                updated_at=CURRENT_TIMESTAMP
            """,
            (
                company_id,
                json.dumps(result.get("tech_stack", [])),
                json.dumps(result.get("recent_news", [])),
                json.dumps(result.get("open_roles", [])),
                result.get("engineering_focus", ""),
                json.dumps(result.get("personalization_hooks", [])),
            ),
        )
        conn.execute("UPDATE companies SET status = 'extracted' WHERE id = ?", (company_id,))
        conn.commit()
    finally:
        conn.close()
