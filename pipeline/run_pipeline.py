"""
Orchestrator — runs each stage over whatever companies are at the right
status. Run manually (`python pipeline/run_pipeline.py`) or put it on a
cron. Nothing here calls another stage directly; every stage reads/writes
the DB, so you can also run any single stage on its own while debugging.
"""
from db.db import get_conn, init_db
from pipeline.research import research_company
from pipeline.extract import extract_research
from pipeline.generate import generate_email
from pipeline.critic import critique_email


def run():
    # TODO: init_db(), then walk companies through each status in order:
    #   new -> research_company
    #   researched -> extract_research
    #   contact_found -> generate_email (contacts aren't auto-discovered, see README)
    #   generated (no critic_notes yet) -> critique_email
    raise NotImplementedError


if __name__ == "__main__":
    run()
