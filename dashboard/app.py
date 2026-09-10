"""
Approval dashboard. Run with: streamlit run dashboard/app.py
Shows generated emails, lets you edit/approve/reject. Nothing sends from
here — sending is a separate, deliberate step (sender/send_approved.py).
"""
import json
import streamlit as st
from db.db import get_conn

st.set_page_config(page_title="Cold Email Review", layout="wide")
st.title("Cold Email Review Queue")

conn = get_conn()
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

conn.close()
