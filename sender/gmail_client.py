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
    # TODO: load cached creds from TOKEN_PATH, refresh or run InstalledAppFlow as needed,
    # cache back to TOKEN_PATH, return build("gmail", "v1", credentials=creds)
    raise NotImplementedError


def send_email(to: str, subject: str, body: str) -> dict:
    # TODO: build MIMEText message, base64url-encode, send via Gmail API
    raise NotImplementedError
