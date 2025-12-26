import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env")

# Константы путей
TRACK_FILE = Path("time.json")
RESUME_FILE = Path("resume.json")
EXTERNAL_URL = "http://your-url-here.com/api"  # ЗАМЕНИ НА СВОЙ URL
