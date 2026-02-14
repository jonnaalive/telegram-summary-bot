"""Google Drive OAuth2로 옵시디언 볼트에 마크다운 저장."""

import json
import os

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaInMemoryUpload

TOKEN_URI = "https://oauth2.googleapis.com/token"


def _get_service():
    token_json = os.getenv("GDRIVE_TOKEN", "")
    if not token_json:
        return None
    token_data = json.loads(token_json)
    creds = Credentials(
        token=None,
        refresh_token=token_data["refresh_token"],
        token_uri=TOKEN_URI,
        client_id=token_data["client_id"],
        client_secret=token_data["client_secret"],
    )
    return build("drive", "v3", credentials=creds)


def _find_or_create_folder(service, folder_name: str, parent_id: str) -> str:
    """폴더를 찾거나 없으면 생성한다."""
    query = (
        f"name='{folder_name}' and '{parent_id}' in parents "
        f"and mimeType='application/vnd.google-apps.folder' and trashed=false"
    )
    results = service.files().list(q=query, fields="files(id)").execute()
    files = results.get("files", [])
    if files:
        return files[0]["id"]

    metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    folder = service.files().create(body=metadata, fields="id").execute()
    return folder["id"]


def upload_to_gdrive(content: str, filename: str) -> str | None:
    """마크다운 파일을 Google Drive 옵시디언 볼트에 업로드한다."""
    service = _get_service()
    if not service:
        print("[!] GDRIVE_TOKEN 미설정, Google Drive 스킵")
        return None

    vault_folder_id = os.getenv("GDRIVE_VAULT_FOLDER_ID", "")
    if not vault_folder_id:
        print("[!] GDRIVE_VAULT_FOLDER_ID 미설정, Google Drive 스킵")
        return None

    # Daily Summary 하위 폴더
    summary_folder_id = _find_or_create_folder(service, "Daily Summary", vault_folder_id)

    # 기존 파일 있으면 업데이트, 없으면 생성
    query = f"name='{filename}' and '{summary_folder_id}' in parents and trashed=false"
    results = service.files().list(q=query, fields="files(id)").execute()
    existing = results.get("files", [])

    media = MediaInMemoryUpload(content.encode("utf-8"), mimetype="text/markdown")

    if existing:
        file = service.files().update(
            fileId=existing[0]["id"], media_body=media
        ).execute()
    else:
        metadata = {
            "name": filename,
            "parents": [summary_folder_id],
        }
        file = service.files().create(
            body=metadata, media_body=media, fields="id"
        ).execute()

    print(f"[+] Google Drive 업로드 완료: {filename}")
    return file.get("id")
