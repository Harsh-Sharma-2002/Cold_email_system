"""
Gmail sending + reading, official API, OAuth. One-time setup:
1. Create a Google Cloud project, enable the Gmail API.
2. Create OAuth client credentials (Desktop app type), download as
   credentials.json into the project root.
3. First run opens a browser to authorize; token.json is cached after that.

pip install google-auth-oauthlib google-api-python-client
"""
import base64
import mimetypes
import os
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
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

# Attached to every outgoing email when the file exists — drop your resume
# PDF here (or point RESUME_ATTACHMENT_PATH at it in .env).
RESUME_PATH = os.environ.get("RESUME_ATTACHMENT_PATH", "resume.pdf")


def get_service(creds_path=CREDS_PATH, token_path=TOKEN_PATH):
    """
    Defaults to the active sending account. Pass a different
    (creds_path, token_path) pair to read another mailbox — e.g. a
    retired account whose old sent threads we still want to poll for
    replies, without touching the token used for actual sending.
    """
    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def send_email(to: str, subject: str, body: str) -> dict:
    if os.path.exists(RESUME_PATH):
        message = MIMEMultipart()
        message.attach(MIMEText(body))

        ctype, encoding = mimetypes.guess_type(RESUME_PATH)
        if ctype is None or encoding is not None:
            ctype = "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)

        with open(RESUME_PATH, "rb") as f:
            part = MIMEBase(maintype, subtype)
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition", "attachment", filename=os.path.basename(RESUME_PATH)
        )
        message.attach(part)
    else:
        message = MIMEText(body)

    message["to"] = to
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    service = get_service()
    return service.users().messages().send(userId="me", body={"raw": raw}).execute()
