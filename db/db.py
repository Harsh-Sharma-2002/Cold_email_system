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
    # TODO: connect, set row_factory = sqlite3.Row, enable foreign_keys
    raise NotImplementedError


def init_db():
    # TODO: run schema.sql against DB_PATH
    raise NotImplementedError


if __name__ == "__main__":
    init_db()
    print(f"Initialized {DB_PATH}")
