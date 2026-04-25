import os
from pathlib import Path
from dotenv import load_dotenv
import yaml

# Project root (two levels up from config directory)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Load environment variables - check for custom ENV_FILE first, then docker folder, then project root
custom_env_file = os.getenv("ENV_FILE")
if custom_env_file:
    load_dotenv(custom_env_file)
else:
    docker_env_path = PROJECT_ROOT / "docker" / ".env"
    if docker_env_path.exists():
        load_dotenv(docker_env_path)
    else:
        load_dotenv()

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Ollama Configuration (Local LLM for settlement reasoning)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma:7b")
OLLAMA_TIMEOUT_SECONDS = 60

# Database Configuration
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
POSTGRES_DB = os.getenv("POSTGRES_DB", "events")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "db")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

# SQLite for local development (fallback)
DATABASE_PATH = os.getenv("DATABASE_PATH", "./betting_bot.db")

# PostgreSQL connection string (for Docker/production)
POSTGRES_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Use DATABASE_URL from env if set, otherwise check for DATABASE_PATH, fallback to PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL", DATABASE_PATH if os.getenv("DATABASE_PATH") else POSTGRES_URL)

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# App Configuration
MAX_USERS_PER_GROUP = 100
MIN_BET_AMOUNT = 0.01
MAX_BET_AMOUNT = 1000000
DECIMAL_PLACES = 2
SETTLEMENT_TIMEOUT_SECONDS = 30

# Load YAML configuration
def load_yaml_config():
    """Load configuration from config.yaml file."""
    config_path = Path(__file__).parent / "config.yaml"
    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return None

# Bot personality and inactivity configuration
_yaml_config = load_yaml_config() or {}
_bot_config = _yaml_config.get('bot', {})

# Version
VERSION = _yaml_config.get('version', '1.0.0')

# Personality configuration
PERSONALITY_ENABLED = _bot_config.get('personality', {}).get('enabled', True)
PERSONALITY_SASSY_LEVEL = _bot_config.get('personality', {}).get('sassy_level', 'medium')
PERSONALITY_USE_LLM = _bot_config.get('personality', {}).get('use_llm', True)

# Inactivity configuration
INACTIVITY_ENABLED = _bot_config.get('inactivity', {}).get('enabled', True)
INACTIVITY_TIMEOUT_MINUTES = _bot_config.get('inactivity', {}).get('timeout_minutes', 30)
INACTIVITY_RANDOM_MESSAGE_INTERVAL_MINUTES = _bot_config.get('inactivity', {}).get('random_message_interval_minutes', 10)
INACTIVITY_MAX_RANDOM_MESSAGES = _bot_config.get('inactivity', {}).get('max_random_messages', 3)

