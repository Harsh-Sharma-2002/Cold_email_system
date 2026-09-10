"""
Orchestrator — runs each stage over whatever companies are at the right
status. Run manually (`python pipeline/run_pipeline.py`) or put it on a
cron. Nothing here calls another stage directly; every stage reads/writes
the DB, so you can also run any single stage on its own while debugging.

Contact discovery is now automatic: extracted companies get a free Apollo
people-search (find_contacts), then up to MAX_VERIFY_PER_COMPANY of those
candidates per company get their email revealed (verify_with_provider,
1 Apollo credit each) — that cap is what keeps this safe to run on a cron
without silently burning through credits.
"""
from urllib.parse import urlparse
from db.db import get_conn, init_db
from pipeline.research import research_company
from pipeline.extract import extract_research
from pipeline.contacts import find_contacts, verify_with_provider, MAX_VERIFY_PER_COMPANY
from pipeline.generate import generate_email
from pipeline.critic import critique_email


def _domain_from_website(website: str | None) -> str | None:
    if not website:
        return None
    netloc = urlparse(website if "://" in website else f"//{website}").netloc or website
    return netloc.removeprefix("www.").split(":")[0]


def run():
    init_db()
    conn = get_conn()
    try:
        new = conn.execute("SELECT id, name, website FROM companies WHERE status = 'new'").fetchall()
        researched = conn.execute("SELECT id FROM companies WHERE status = 'researched'").fetchall()
        extracted = conn.execute(
            "SELECT id, website, domain FROM companies WHERE status = 'extracted'"
        ).fetchall()
        verify_candidates = conn.execute(
            """
            SELECT id FROM (
                SELECT ct.id,
                       ROW_NUMBER() OVER (PARTITION BY ct.company_id ORDER BY ct.id) AS rn
                FROM contacts ct
                JOIN companies co ON co.id = ct.company_id
                WHERE co.status = 'contact_found' AND ct.email IS NULL
            )
            WHERE rn <= ?
            """,
            (MAX_VERIFY_PER_COMPANY,),
        ).fetchall()
        ready_to_generate = conn.execute(
            "SELECT c.id AS company_id, ct.id AS contact_id "
            "FROM companies c JOIN contacts ct ON ct.company_id = c.id "
            "WHERE c.status = 'contact_found' AND ct.email IS NOT NULL"
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

    for row in extracted:
        domain = row["domain"] or _domain_from_website(row["website"])
        if not domain:
            continue
        conn = get_conn()
        try:
            conn.execute("UPDATE companies SET domain = ? WHERE id = ?", (domain, row["id"]))
            conn.commit()
        finally:
            conn.close()
        find_contacts(row["id"], domain)

    for row in verify_candidates:
        verify_with_provider(row["id"])

    for row in ready_to_generate:
        generate_email(row["company_id"], row["contact_id"])

    for row in ungenerated_critiques:
        critique_email(row["id"])


if __name__ == "__main__":
    run()
