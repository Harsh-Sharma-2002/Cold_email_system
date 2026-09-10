"""
Orchestrator — runs each stage over whatever companies are at the right
status. Run manually (`python pipeline/run_pipeline.py`) or put it on a
cron. Nothing here calls another stage directly; every stage reads/writes
the DB, so you can also run any single stage on its own while debugging.
"""
from db.db import get_conn, init_db
from pipeline.research import research_company
from pipeline.extract import extract_research
from pipeline.generate import generate_email
from pipeline.critic import critique_email


def run():
    init_db()
    conn = get_conn()
    try:
        new = conn.execute("SELECT id, name, website FROM companies WHERE status = 'new'").fetchall()
        researched = conn.execute("SELECT id FROM companies WHERE status = 'researched'").fetchall()
        ready_to_generate = conn.execute(
            "SELECT c.id AS company_id, ct.id AS contact_id "
            "FROM companies c JOIN contacts ct ON ct.company_id = c.id "
            "WHERE c.status = 'contact_found'"
        ).fetchall()
        ungenerated_critiques = conn.execute(
            "SELECT id FROM generated_emails WHERE critic_notes IS NULL"
        ).fetchall()
    finally:
        conn.close()

    for row in new:
        research_company(row["id"], row["name"], row["website"])

    for row in researched:
        extract_research(row["id"])

    for row in ready_to_generate:
        generate_email(row["company_id"], row["contact_id"])

    for row in ungenerated_critiques:
        critique_email(row["id"])


if __name__ == "__main__":
    run()
