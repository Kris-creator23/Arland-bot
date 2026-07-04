from pathlib import Path
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN not found")

ADMIN_ID = int(os.environ.get("ADMIN_ID"))

BASE_DIR = Path(__file__).parent

USERS_FILE = BASE_DIR / "users.json"

MEDIA_DIR = BASE_DIR / "media"

PASSPORTS_DIR = MEDIA_DIR / "passports"

RECEIPTS_DIR = MEDIA_DIR / "receipts"

INSTRUCTION_IMAGE = BASE_DIR / "instructions.jpg"