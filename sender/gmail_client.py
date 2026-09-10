"""
Gmail sending + reading, official API, OAuth. One-time setup:
1. Create a Google Cloud project, enable the Gmail API.
2. Create OAuth client credentials (Desktop app type), download as
   credentials.json into the project root.
3. First run opens a browser to authorize; token.json is cached after that.

pip install google-auth-oauthlib google-api-python-client
"""
import base64
import os
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# send + readonly so reply_tracker.py can poll threads with the same auth
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
]
TOKEN_PATH = "token.json"
CREDS_PATH = "credentials.json"


def get_service():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def send_email(to: str, subject: str, body: str) -> dict:
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    service = get_service()
    return service.users().messages().send(userId="me", body={"raw": raw}).execute()
