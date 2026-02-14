"""Google Drive OAuth2 인증 - 최초 1회 실행하여 refresh token 획득."""

import json

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

CLIENT_CONFIG = {
    "installed": {
        "client_id": "944331716202-h3odg015v2ead31moh2u8bjsgjf5a9fi.apps.googleusercontent.com",
        "project_id": "telemdmamker",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_secret": "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",
        "redirect_uris": ["http://localhost"],
    }
}


def main():
    flow = InstalledAppFlow.from_client_config(CLIENT_CONFIG, SCOPES)
    creds = flow.run_local_server(port=0)

    token_data = {
        "client_id": CLIENT_CONFIG["installed"]["client_id"],
        "client_secret": CLIENT_CONFIG["installed"]["client_secret"],
        "refresh_token": creds.refresh_token,
    }
    print("\n=== 아래 JSON을 GitHub Secret GDRIVE_TOKEN 에 등록하세요 ===")
    print(json.dumps(token_data))
    print("=============================================================")


if __name__ == "__main__":
    main()
