import os
from pathlib import Path
from dotenv import load_dotenv

BASE = Path(__file__).parent.parent
load_dotenv(BASE / ".env")

DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DS_URL = "https://api.deepseek.com/chat/completions"
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./prompt_hub.db")
SECRET_TOKEN = os.getenv("SECRET_TOKEN", "prompt-hub-admin-token")
PORT = int(os.getenv("PORT", "8000"))
