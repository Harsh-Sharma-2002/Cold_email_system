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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    source TEXT,                  -- 'pattern_guess' | 'apollo' | 'hunter' | 'manual'
    confidence REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS generated_emails (
    id INTEGER PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    contact_id INTEGER NOT NULL REFERENCES contacts(id),
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
