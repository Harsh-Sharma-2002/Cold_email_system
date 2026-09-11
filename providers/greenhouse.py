"""
Greenhouse Job Board API — public, read-only, no API key required.

Used to discover real open roles at companies that use Greenhouse, so
outreach can reference an actual posting instead of a generic "interested
in engineering roles". Submitting applications through Greenhouse's API
requires a key issued by the *employer's own* account (not something an
applicant can obtain), so this provider is read-only by design — actually
applying still happens through the real posting URL.

pip install requests
"""
import requests

BASE_URL = "https://boards-api.greenhouse.io/v1/boards"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; student-job-search-bot/0.1)"}


def board_exists(board_token: str) -> bool:
    """Cheap check for whether a company's Greenhouse board token is valid."""
    resp = requests.get(f"{BASE_URL}/{board_token}/jobs", headers=HEADERS, timeout=10)
    return resp.status_code == 200


def list_jobs(board_token: str) -> list[dict]:
    """Returns open roles as {id, title, url, department, location, content, updated_at}."""
    resp = requests.get(
        f"{BASE_URL}/{board_token}/jobs",
        params={"content": "true"},
        headers=HEADERS,
        timeout=15,
    )
    resp.raise_for_status()
    jobs = resp.json().get("jobs", [])
    return [
        {
            "id": str(j["id"]),
            "title": j.get("title"),
            "url": j.get("absolute_url"),
            "department": (j.get("departments") or [{}])[0].get("name"),
            "location": (j.get("location") or {}).get("name"),
            "content": j.get("content"),
            "updated_at": j.get("updated_at"),
        }
        for j in jobs
    ]
