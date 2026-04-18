import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project root
PROJECT_ROOT = Path(__file__).parent

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Ollama Configuration (Local LLM for settlement reasoning)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma:7b")
OLLAMA_TIMEOUT_SECONDS = 60

# Database Configuration
DATABASE_PATH = os.getenv("DATABASE_PATH", str(PROJECT_ROOT / "betting_bot.db"))

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# App Configuration
MAX_USERS_PER_GROUP = 100
MIN_BET_AMOUNT = 0.01
MAX_BET_AMOUNT = 1000000
DECIMAL_PLACES = 2
SETTLEMENT_TIMEOUT_SECONDS = 30
