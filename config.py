import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
EXTERNAL_URL = os.getenv("EXTERNAL_URL")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env")

if not EXTERNAL_URL:
    raise ValueError("EXTERNAL_URL не найден в .env")

# Константы путей
TRACK_FILE = Path("time.json")
RESUME_FILE = Path("resume.json")
