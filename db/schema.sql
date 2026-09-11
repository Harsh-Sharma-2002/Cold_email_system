-- Companies being worked through the pipeline.
-- status moves: new -> researched -> extracted -> contact_found
--               -> email_generated -> approved -> sent -> replied
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    website TEXT,
    domain TEXT,
    status TEXT NOT NULL DEFAULT 'new',
    last_researched TIMESTAMP,
    greenhouse_board_token TEXT,  -- the slug in boards.greenhouse.io/{token}, once discovered
    greenhouse_checked_at TIMESTAMP,  -- when we last tried to find/refresh this, even if it failed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Open roles pulled from a company's public Greenhouse job board (read-only,
-- no API key needed — see providers/greenhouse.py). Lets outreach reference
-- an actual open req instead of a generic "interested in engineering roles".
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    greenhouse_job_id TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT,
    department TEXT,
    location TEXT,
    description TEXT,             -- stripped job description HTML->text, for matching + email hooks
    status TEXT NOT NULL DEFAULT 'new',  -- new | targeted | closed
    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(company_id, greenhouse_job_id)
);

-- Never throw away retrieved data. If prompts improve later, rerun
-- extraction against this table for free — no new API calls.
CREATE TABLE IF NOT EXISTS evidence (
    id INTEGER PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    source TEXT NOT NULL,        -- 'search' | 'website'
    url TEXT,
    raw_content TEXT,
    retrieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- One structured research row per company, produced from evidence by the LLM.
CREATE TABLE IF NOT EXISTS research (
    company_id INTEGER PRIMARY KEY REFERENCES companies(id),
    tech_stack TEXT,              -- JSON array, stored as text
    recent_news TEXT,             -- JSON array
    open_roles TEXT,              -- JSON array
    engineering_focus TEXT,
    personalization_hooks TEXT,   -- JSON array
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    name TEXT,
    title TEXT,
    linkedin TEXT,
    email TEXT,
    email_verified BOOLEAN DEFAULT 0,
    source TEXT,                  -- 'pattern_guess' | 'apollo_search' | 'apollo' | 'hunter' | 'manual'
    confidence REAL,
    external_id TEXT,             -- provider's person id (e.g. Apollo), set by apollo_search,
                                   -- used to enrich-by-id later without spending a match credit on name lookup
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS generated_emails (
    id INTEGER PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    contact_id INTEGER NOT NULL REFERENCES contacts(id),
    job_id INTEGER REFERENCES jobs(id),  -- specific open role this email is about, if any
    subject TEXT,
    body TEXT,
    critic_notes TEXT,            -- JSON: {"approved": bool, "issues": [...]}
    status TEXT NOT NULL DEFAULT 'generated',  -- generated | approved | rejected | sent | replied
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    sent_at TIMESTAMP,
    gmail_thread_id TEXT,
    gmail_message_id TEXT
);

-- Enrichment provider key pool — see providers/enrichment.py.
-- Add rows as you burn through free tier -> trial -> next account.
CREATE TABLE IF NOT EXISTS api_keys (
    id INTEGER PRIMARY KEY,
    provider TEXT NOT NULL,
    key TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',  -- active | exhausted | disabled
    last_used TIMESTAMP
);
