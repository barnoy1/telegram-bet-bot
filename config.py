import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project root
PROJECT_ROOT = Path(__file__).parent

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Copilot Configuration
COPILOT_CLI_PATH = os.getenv("COPILOT_CLI_PATH", "copilot")
COPILOT_AUTH_TOKEN = os.getenv("COPILOT_AUTH_TOKEN", "")

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
