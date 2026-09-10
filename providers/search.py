"""
Web search provider — Tavily by default (1,000 free credits/month, no
card, built for feeding LLM pipelines). Swap to another vendor by editing
only this file; nothing else calls a search API directly.

Company research only — people-finding goes through Apollo's free search
instead (see pipeline/contacts.py), so Tavily credits are spent solely on
the one query per company that research_company() fires.

pip install tavily-python python-dotenv
"""
import os
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()
_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

# Steers the single search query toward recruiting-relevant signal (tech
# stack, news, hiring) instead of a bare company-name search that mostly
# returns marketing pages.
QUERY_TEMPLATE = "{company_name} engineering team tech stack recent news hiring {extra_terms}"

# How far back Tavily should look — keeps evidence from going stale.
# One of: day, week, month, year. Override via .env.
SEARCH_TIME_RANGE = os.environ.get("SEARCH_TIME_RANGE", "year")


def search_company(company_name: str, extra_terms: str = "", max_results: int = 5):
    """Returns a list of {title, url, content} dicts."""
    query = QUERY_TEMPLATE.format(company_name=company_name, extra_terms=extra_terms).strip()
    results = _client.search(query, max_results=max_results, time_range=SEARCH_TIME_RANGE)
    return [
        {"title": r.get("title"), "url": r.get("url"), "content": r.get("content")}
        for r in results.get("results", [])
    ]
