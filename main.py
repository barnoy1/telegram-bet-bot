"""Main entry point for Telegram betting bot."""

import asyncio
import logging
import sys
from pathlib import Path

from telegram.ext import Application, CommandHandler, ContextTypes

from config import TELEGRAM_BOT_TOKEN, DATABASE_PATH, COPILOT_CLI_PATH, LOG_LEVEL
from bot.group_manager import GroupManager
from bot.telegram_handler import BettingHandler, BETTING, RESULTS, SETTLE
from db.storage import BettingStorage
from settlement.copilot_agent import CopilotSettlementAgent

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    """Start the Telegram bot."""
    logger.info("Starting Betting Bot...")

    # Initialize storage and managers
    storage = BettingStorage(DATABASE_PATH)
    group_manager = GroupManager(storage)

    # Initialize Copilot agent (non-blocking if unavailable)
    copilot_agent = CopilotSettlementAgent(cli_path=COPILOT_CLI_PATH)
    copilot_available = await copilot_agent.initialize()
    logger.info(f"Copilot agent available: {copilot_available}")

    # Initialize handlers
    betting_handler = BettingHandler(group_manager, copilot_agent if copilot_available else None)

    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", betting_handler.start))
    application.add_handler(CommandHandler("bet", betting_handler.bet))
    application.add_handler(CommandHandler("close", betting_handler.close))
    application.add_handler(CommandHandler("winner", betting_handler.winner))
    application.add_handler(CommandHandler("settle", betting_handler.settle))
    application.add_handler(CommandHandler("status", betting_handler.status))
    application.add_handler(CommandHandler("transactions", betting_handler.transactions))

    # Start bot
    logger.info("Bot is running. Press Ctrl+C to stop.")
    try:
        await application.run_polling()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
        await application.stop()


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
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
