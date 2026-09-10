"""
Plain-text scraper for company websites — free, no vendor lock-in, no
API key. Falls back gracefully if a page can't be fetched or parsed.

pip install requests trafilatura
"""
import requests
import trafilatura

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; student-research-bot/0.1)"}


def fetch_page_text(url: str, timeout: int = 10):
    # TODO: GET url, return None on request failure, else trafilatura.extract(resp.text)
    raise NotImplementedError
