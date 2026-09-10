"""
Plain-text scraper for company websites — free, no vendor lock-in, no
API key. Falls back gracefully if a page can't be fetched or parsed.

pip install requests trafilatura
"""
import requests
import trafilatura

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; student-research-bot/0.1)"}


def fetch_page_text(url: str, timeout: int = 10):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
    except requests.RequestException:
        return None
    return trafilatura.extract(resp.text)
