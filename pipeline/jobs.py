"""
Job discovery. Finds a company's Greenhouse board (if it has one) and pulls
its open roles into the jobs table, so outreach can reference an actual
req instead of talking about the company only in the abstract. Read-only —
actually applying still happens through the real posting URL.
"""
import html
import re
from db.db import get_conn
from providers import greenhouse

# Rough filter for which open roles are worth referencing in outreach —
# adjust to taste. Everything still gets stored; this only affects which
# jobs get suggested as the "hook" for an email.
RELEVANT_TITLE_KEYWORDS = [
    "software engineer", "swe", "backend", "back-end", "full stack",
    "full-stack", "platform engineer", "infrastructure", "machine learning",
    "ml engineer", "ai engineer", "data engineer", "research engineer",
    "systems engineer", "site reliability", "devops", "cloud engineer",
]


def _strip_html(content: str | None) -> str | None:
    if not content:
        return None
    text = re.sub(r"<[^>]+>", " ", content)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _candidate_tokens(name: str) -> list[str]:
    """Likely Greenhouse board-token slugs to try for a company name."""
    words = re.findall(r"[a-z0-9]+", name.lower())
    candidates = ["".join(words)]
    if len(words) > 1:
        candidates.append("-".join(words))
        candidates.append(words[0])
    seen = set()
    return [c for c in candidates if c and not (c in seen or seen.add(c))]


def find_board_token(company_id: int, company_name: str) -> str | None:
    """Tries likely slugs and stores the first one that resolves. Marks
    greenhouse_checked_at either way so a future run doesn't retry a
    company that simply isn't on Greenhouse."""
    conn = get_conn()
    try:
        for token in _candidate_tokens(company_name):
            if greenhouse.board_exists(token):
                conn.execute(
                    "UPDATE companies SET greenhouse_board_token = ?, "
                    "greenhouse_checked_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (token, company_id),
                )
                conn.commit()
                return token
        conn.execute(
            "UPDATE companies SET greenhouse_checked_at = CURRENT_TIMESTAMP WHERE id = ?",
            (company_id,),
        )
        conn.commit()
        return None
    finally:
        conn.close()


def discover_jobs(company_id: int, board_token: str) -> int:
    """Pulls open roles for a company's Greenhouse board, upserts into
    jobs (dedup on greenhouse_job_id). Returns how many jobs were found."""
    postings = greenhouse.list_jobs(board_token)
    conn = get_conn()
    try:
        for j in postings:
            conn.execute(
                """
                INSERT INTO jobs (company_id, greenhouse_job_id, title, url,
                                   department, location, description, last_seen_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(company_id, greenhouse_job_id) DO UPDATE SET
                    title=excluded.title, url=excluded.url,
                    department=excluded.department, location=excluded.location,
                    description=excluded.description, last_seen_at=CURRENT_TIMESTAMP
                """,
                (
                    company_id, j["id"], j["title"], j["url"],
                    j["department"], j["location"], _strip_html(j["content"]),
                ),
            )
        conn.commit()
        return len(postings)
    finally:
        conn.close()


def relevant_jobs(company_id: int) -> list:
    """Open roles for a company whose title matches RELEVANT_TITLE_KEYWORDS,
    most recently seen first — a reasonable default pick for outreach."""
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM jobs WHERE company_id = ? ORDER BY last_seen_at DESC",
            (company_id,),
        ).fetchall()
    finally:
        conn.close()
    return [
        r for r in rows
        if any(k in (r["title"] or "").lower() for k in RELEVANT_TITLE_KEYWORDS)
    ]
