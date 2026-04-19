"""Main entry point for Telegram betting bot."""

import asyncio
import logging
import sys
from pathlib import Path

from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from config import TELEGRAM_BOT_TOKEN, DATABASE_PATH, OLLAMA_BASE_URL, OLLAMA_MODEL, LOG_LEVEL
from bot.group_manager import GroupManager
from bot.telegram_handler import BettingHandler, BETTING, RESULTS, SETTLE
from db.storage import BettingStorage
from settlement.ollama_agent import OllamaSettlementAgent

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Start the Telegram bot."""
    logger.info("Starting Betting Bot...")

    # Initialize storage and managers
    storage = BettingStorage(DATABASE_PATH)
    group_manager = GroupManager(storage)

    # Initialize Ollama agent (non-blocking if unavailable)
    ollama_agent = OllamaSettlementAgent(base_url=OLLAMA_BASE_URL, model=OLLAMA_MODEL)
    ollama_available = asyncio.run(ollama_agent.initialize())
    logger.info(f"Ollama agent available: {ollama_available}")

    # Initialize handlers
    betting_handler = BettingHandler(group_manager, ollama_agent if ollama_available else None)

    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("str", betting_handler.start))
    application.add_handler(CommandHandler("h", betting_handler.help))
    application.add_handler(CommandHandler("b", betting_handler.bet))
    application.add_handler(CommandHandler("w", betting_handler.winner))
    application.add_handler(CommandHandler("s", betting_handler.settle))
    application.add_handler(CommandHandler("sts", betting_handler.status))
    application.add_handler(CommandHandler("t", betting_handler.transactions))
    application.add_handler(CommandHandler("u", betting_handler.undo))
    application.add_handler(CommandHandler("r", betting_handler.reset))

    # Register message handlers
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^\d+(\.\d+)?$'), betting_handler.handle_numeric_message))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, betting_handler.new_chat_members))

    # Start bot
    logger.info("Bot is running. Press Ctrl+C to stop.")
    try:
        # Create new event loop for the bot
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        application.run_polling()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")


def validate_config():
    """Validate required configuration."""
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "your_telegram_bot_token_here":
        logger.error("TELEGRAM_BOT_TOKEN not configured in .env")
        return False
    return True


if __name__ == "__main__":
    if not validate_config():
        sys.exit(1)

    try:
        main()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
