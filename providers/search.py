"""
Web search provider — Tavily by default (1,000 free credits/month, no
card, built for feeding LLM pipelines). Swap to another vendor by editing
only this file; nothing else calls a search API directly.

pip install tavily-python python-dotenv
"""
import os
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()
_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])


def search_company(company_name: str, extra_terms: str = "", max_results: int = 5):
    """Returns a list of {title, url, content} dicts."""
    query = f"{company_name} {extra_terms}".strip()
    results = _client.search(query, max_results=max_results)
    return [
        {"title": r.get("title"), "url": r.get("url"), "content": r.get("content")}
        for r in results.get("results", [])
    ]
