import os
from pathlib import Path

from dotenv import load_dotenv

# Загружаем переменные окружения из .env рядом с config.py
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Токен Telegram-бота
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Ключ для DashScope (Qwen)
QWEN_API_KEY = os.getenv("QWEN_API_KEY")

# Настройки модели Qwen
QWEN_ENDPOINT = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
QWEN_MODEL = "qwen-turbo"

# Провайдер генерации: qwen / ollama / local (если не задан, выбирается автоматически)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "").strip().lower()

# Настройки Ollama (локальный открытый инструмент)
OLLAMA_ENDPOINT = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")

# Целевой баланс коммуникативных упражнений
TARGET_COMMUNICATIVE_RATIO = 0.5
