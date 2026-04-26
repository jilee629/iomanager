#!/usr/bin/env -S uv run python

from pathlib import Path
from datetime import datetime
import json, os

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload
from googleapiclient.discovery import build

BASE_DIR = Path(__file__).resolve().parent.parent

def authenticate_google_drive():
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    creds = None

    token_file = os.path.join(BASE_DIR, 'token.json')
    credentials_file = os.path.join(BASE_DIR, 'credentials.json')

    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_file, 'w') as token:
            token.write(creds.to_json())
    return creds

def create_drive_folder(folder_name):
    creds = authenticate_google_drive()
    service = build('drive', 'v3', credentials=creds)
    
    file_metadata = {
                    'name': folder_name,
                    "mimeType": "application/vnd.google-apps.folder",
                    'parents': ['1Wwb3CYQ7OnCp5hWboVXELPxbxtAbXP9R']
                    }

    file = service.files().create(body=file_metadata, fields="id").execute()
    folder_id = file.get("id")
    return folder_id

def upload_file(folder_id, file_name, mtype=None):
    creds = authenticate_google_drive()
    service = build('drive', 'v3', credentials=creds)

    local_file_path = os.path.join(BASE_DIR, file_name)
    mimetype='application/x-sqlite3'
    media = MediaFileUpload(local_file_path, mimetype=mimetype, resumable=True)
    drive_file_name = file_name
    file_metadata = {
                    'name': drive_file_name,
                    'parents': [folder_id]
                    }

    file = service.files().create(body=file_metadata, media_body=media, fields='id, name').execute()
    file.get('id')
    print(f'UPLOADING {file_name} IS OK.')
    return True

file_date = datetime.now().strftime("%Y-%m-%d")
folder_id = create_drive_folder(file_date)

file_name = 'db.sqlite3'
upload_file(folder_id, file_name, mtype='sqlite3')
