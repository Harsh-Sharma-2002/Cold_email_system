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
    # TODO: search_company -> insert evidence rows (source='search')
    # TODO: for each PAGES_TO_TRY path off website -> fetch_page_text -> insert evidence (source='website')
    # TODO: mark company status='researched', last_researched=now
    raise NotImplementedError
