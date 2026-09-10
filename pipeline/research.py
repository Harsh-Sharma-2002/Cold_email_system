"""
Stage 1: Retrieve. Search + scrape -> evidence table. No LLM here — keep
raw retrieval separate from reasoning, so re-running extraction later
(better prompts, different model) never costs another search or scrape.
"""
from db.db import get_conn
from providers.search import search_company
from providers.scraper import fetch_page_text

PAGES_TO_TRY = ["", "/about", "/careers", "/blog", "/engineering"]


def research_company(company_id: int, name: str, website: str | None):
    conn = get_conn()
    try:
        for r in search_company(name):
            conn.execute(
                "INSERT INTO evidence (company_id, source, url, raw_content) VALUES (?, 'search', ?, ?)",
                (company_id, r["url"], r["content"]),
            )

        if website:
            base = website.rstrip("/")
            for path in PAGES_TO_TRY:
                text = fetch_page_text(base + path)
                if text:
                    conn.execute(
                        "INSERT INTO evidence (company_id, source, url, raw_content) VALUES (?, 'website', ?, ?)",
                        (company_id, base + path, text),
                    )

        conn.execute(
            "UPDATE companies SET status = 'researched', last_researched = CURRENT_TIMESTAMP WHERE id = ?",
            (company_id,),
        )
        conn.commit()
    finally:
        conn.close()
