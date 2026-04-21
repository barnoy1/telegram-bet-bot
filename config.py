import os
from pathlib import Path
from dotenv import load_dotenv
import yaml

# Project root
PROJECT_ROOT = Path(__file__).parent

# Load environment variables - try docker folder first (for Docker context), then project root
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
DATABASE_PATH = os.getenv("DATABASE_PATH", str(PROJECT_ROOT / "betting_bot.db"))

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
    config_path = PROJECT_ROOT / "config.yaml"
    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return None

# Bot personality and inactivity configuration
_yaml_config = load_yaml_config() or {}
_bot_config = _yaml_config.get('bot', {})

# Personality configuration
PERSONALITY_ENABLED = _bot_config.get('personality', {}).get('enabled', True)
PERSONALITY_SASSY_LEVEL = _bot_config.get('personality', {}).get('sassy_level', 'medium')

# Inactivity configuration
INACTIVITY_ENABLED = _bot_config.get('inactivity', {}).get('enabled', True)
INACTIVITY_TIMEOUT_MINUTES = _bot_config.get('inactivity', {}).get('timeout_minutes', 30)
INACTIVITY_RANDOM_MESSAGE_INTERVAL_MINUTES = _bot_config.get('inactivity', {}).get('random_message_interval_minutes', 10)
INACTIVITY_MAX_RANDOM_MESSAGES = _bot_config.get('inactivity', {}).get('max_random_messages', 3)
