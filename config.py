import os
from dotenv import load_dotenv

load_dotenv()

# --- MAIN CONFIG ---
SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-fast-kanban-key")
ALGORITHM = "HS256"

# Адрес твоего сайта (для генерации ссылки в боте)
# Если запускаешь локально — http://127.0.0.1:8000
# Если на сервере — https://твой-домен.ру
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")

# --- TELEGRAM CONFIG ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_TG_ID = os.getenv("ADMIN_TG_ID")
bot_name = os.getenv("BOT_NAME", "FastKanbanBot") # Имя бота без @, чтобы генерировать ссылки

# --- GEMINI API CONFIG ---
GEMINI_API_URL = os.getenv("GEMINI_API_URL", "https://127.0.0.1:8000")
if GEMINI_API_URL:
    GEMINI_API_URL = GEMINI_API_URL.rstrip("/")

# --- AI PROMPTS ---
PROMPT_BREAKDOWN = (
    "Ты - опытный менеджер. Твоя задача: прослушать аудиозапись цели и разбить её на пошаговый план. "
    "Правила вывода: "
    "1. ТОЛЬКО список задач. "
    "2. Каждый пункт с новой строки. "
    "3. Без нумерации. "
    "4. Без лишних слов. "
    "5. Максимум 7 пунктов."
)

PROMPT_IDEAS = (
    "Ты - креативный помощник. Твоя задача: прослушать аудиозапись и придумать идеи на её основе для канбан-доски. "
    "Правила вывода: "
    "1. ТОЛЬКО список идей. "
    "2. Каждый пункт с новой строки. "
    "3. Без нумерации. "
    "4. Кратко и емко. "
    "5. 3-5 вариантов."
)