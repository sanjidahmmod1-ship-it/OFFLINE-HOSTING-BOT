import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID_RAW = os.getenv("ADMIN_ID", "8452363365").strip()
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "").strip()

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing. Set it in .env")
if not ADMIN_ID_RAW.isdigit():
    raise RuntimeError("ADMIN_ID must be your numeric Telegram user ID")
if not ENCRYPTION_KEY:
    raise RuntimeError("ENCRYPTION_KEY is missing. Generate a Fernet key.")

ADMIN_ID = int(ADMIN_ID_RAW)
