import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OBSIDIAN_VAULT_PATH = os.getenv("OBSIDIAN_VAULT_PATH", "")
FOLDER_NAMES = [name.strip() for name in os.getenv("FOLDER_NAMES", "FOLLOW").split(",")]
