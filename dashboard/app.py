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

# TODO: query generated_emails joined with companies/contacts where status='generated'
# TODO: render each as an expander with subject/body editable fields,
#       critic warnings, and Approve/Reject buttons that update status
