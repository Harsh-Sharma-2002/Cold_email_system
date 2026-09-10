"""
Shared DB connection. Every other module gets its connection from here —
one schema, one place that knows the file path.

pip install python-dotenv
"""
import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.environ.get("DB_PATH", "./leads.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_conn()
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Initialized {DB_PATH}")
