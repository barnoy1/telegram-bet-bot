"""Main entry point for Telegram betting bot."""

import asyncio
import logging
import sys
from pathlib import Path

from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from config import TELEGRAM_BOT_TOKEN, DATABASE_PATH, OLLAMA_BASE_URL, OLLAMA_MODEL, LOG_LEVEL, INACTIVITY_ENABLED
from bot.telegram_handler import BettingHandler, BETTING
from db.storage import BettingStorage
from settlement.ollama_agent import OllamaSettlementAgent
from bot.factories.service_factory import ServiceFactory
from bot.factories.handler_factory import HandlerFactory
from bot.services.inactivity_monitor import InactivityMonitor

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Start the Telegram bot."""
    logger.info("Starting Betting Bot...")

    # Initialize storage
    storage = BettingStorage(DATABASE_PATH)

    # Initialize Ollama agent (non-blocking if unavailable)
    ollama_agent = OllamaSettlementAgent(base_url=OLLAMA_BASE_URL, model=OLLAMA_MODEL)
    ollama_available = asyncio.run(ollama_agent.initialize())
    logger.info(f"Ollama agent available: {ollama_available}")

    # Create service layer using factory
    betting_service, personality = ServiceFactory.create_betting_service(
        storage,
        ollama_agent if ollama_available else None
    )

    # Create command registry using factory
    command_registry = HandlerFactory.create_registry(betting_service, personality)

    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Initialize inactivity monitor
    inactivity_monitor = None
    if INACTIVITY_ENABLED:
        inactivity_monitor = InactivityMonitor(application.bot, personality, storage)

    # Initialize handlers
    betting_handler = BettingHandler(betting_service, command_registry, personality, inactivity_monitor)

    # Register command handlers
    application.add_handler(CommandHandler("str", betting_handler.start))
    application.add_handler(CommandHandler("h", betting_handler.help))
    application.add_handler(CommandHandler("out", betting_handler.out))
    application.add_handler(CommandHandler("sts", betting_handler.status))
    application.add_handler(CommandHandler("t", betting_handler.transactions))
    application.add_handler(CommandHandler("u", betting_handler.undo))
    application.add_handler(CommandHandler("r", betting_handler.reset))

    # Register message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, betting_handler.handle_numeric_message))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, betting_handler.new_chat_members))

    # Start bot
    logger.info("Bot is running. Press Ctrl+C to stop.")
    
    async def main_loop():
        """Main async loop that runs both bot and inactivity monitor."""
        # Start inactivity monitor if enabled
        if inactivity_monitor:
            await inactivity_monitor.start()
        
        # Run the bot
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        
        try:
            # Keep running until interrupted
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("Received cancellation signal")
        finally:
            # Stop inactivity monitor
            if inactivity_monitor:
                await inactivity_monitor.stop()
            await application.updater.stop()
            await application.stop()
            await application.shutdown()
    
    try:
        asyncio.run(main_loop())
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
