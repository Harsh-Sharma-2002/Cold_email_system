"""
Approval dashboard. Run with: streamlit run dashboard/app.py
Shows generated emails, lets you edit/approve/reject. Nothing sends from
here — sending is a separate, deliberate step (sender/send_approved.py).
"""
import json
import os
import sys

# `streamlit run` puts this file's own directory on sys.path, not the
# project root, so the db/providers imports below need this to resolve.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from db.db import get_conn

st.set_page_config(page_title="Cold Email Review", layout="wide")
st.title("Cold Email")

conn = get_conn()

tab_queue, tab_report = st.tabs(["Review Queue", "Report"])

with tab_queue:
    rows = conn.execute(
        """
        SELECT ge.id, ge.subject, ge.body, ge.critic_notes,
               co.name AS company_name, ct.name AS contact_name, ct.email AS contact_email
        FROM generated_emails ge
        JOIN companies co ON co.id = ge.company_id
        JOIN contacts ct ON ct.id = ge.contact_id
        WHERE ge.status = 'generated'
        ORDER BY ge.generated_at
        """
    ).fetchall()

    if not rows:
        st.info("Nothing waiting for review.")

    for row in rows:
        with st.expander(f"{row['company_name']} — {row['contact_name']} ({row['subject']})"):
            critic = json.loads(row["critic_notes"]) if row["critic_notes"] else None
            if critic is None:
                st.caption("No critic review yet.")
            elif critic.get("approved"):
                st.success("Critic: no issues flagged")
            else:
                st.warning("Critic flagged issues:")
            for issue in (critic or {}).get("issues", []):
                st.write(f"- {issue}")

            subject = st.text_input("Subject", value=row["subject"], key=f"subject_{row['id']}")
            body = st.text_area("Body", value=row["body"], height=200, key=f"body_{row['id']}")
            st.caption(f"To: {row['contact_email']}")

            col1, col2 = st.columns(2)
            if col1.button("Approve", key=f"approve_{row['id']}"):
                conn.execute(
                    "UPDATE generated_emails SET subject = ?, body = ?, status = 'approved', "
                    "approved_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (subject, body, row["id"]),
                )
                conn.commit()
                st.rerun()
            if col2.button("Reject", key=f"reject_{row['id']}"):
                conn.execute(
                    "UPDATE generated_emails SET status = 'rejected' WHERE id = ?", (row["id"],)
                )
                conn.commit()
                st.rerun()

with tab_report:
    counts = {
        r["status"]: r["c"]
        for r in conn.execute(
            "SELECT status, COUNT(*) AS c FROM generated_emails GROUP BY status"
        ).fetchall()
    }
    total = sum(counts.values())

    st.caption(f"{total} emails generated in total")
    cols = st.columns(6)
    cols[0].metric("Sent", counts.get("sent", 0))
    cols[1].metric("Replied", counts.get("replied", 0))
    cols[2].metric("Bounced", counts.get("bounced", 0))
    cols[3].metric("Approved (not yet sent)", counts.get("approved", 0))
    cols[4].metric("Pending review", counts.get("generated", 0))
    cols[5].metric("Rejected", counts.get("rejected", 0))

    if st.button("Refresh"):
        st.rerun()

    st.divider()

    status_filter = st.multiselect(
        "Filter by status",
        options=sorted(counts.keys()),
        default=[s for s in ("sent", "replied", "bounced") if s in counts],
    )

    if status_filter:
        placeholders = ",".join("?" * len(status_filter))
        detail_rows = conn.execute(
            f"""
            SELECT ge.status, co.name AS company_name, ct.name AS contact_name,
                   ct.email AS contact_email, ge.subject, ge.sent_at, ge.gmail_thread_id
            FROM generated_emails ge
            JOIN companies co ON co.id = ge.company_id
            JOIN contacts ct ON ct.id = ge.contact_id
            WHERE ge.status IN ({placeholders})
            ORDER BY ge.sent_at DESC, ge.generated_at DESC
            """,
            status_filter,
        ).fetchall()

        st.table(
            [
                {
                    "Status": r["status"],
                    "Company": r["company_name"],
                    "Contact": r["contact_name"],
                    "Email": r["contact_email"],
                    "Subject": r["subject"],
                    "Sent At": r["sent_at"] or "",
                }
                for r in detail_rows
            ]
        )
    else:
        st.info("Select at least one status above to see details.")

conn.close()
