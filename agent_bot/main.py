"""Main entry point for Telegram poker bot."""

import argparse
import sys
from pathlib import Path

# Check for version flag before heavy imports
parser = argparse.ArgumentParser(description="Telegram Poker Bot")
parser.add_argument('-v', '--version', action='store_true', help='Print version and exit')
args = parser.parse_args()

if args.version:
    # Import only settings to get version
    from agent_bot.config.settings import VERSION
    print(f"Poker Bot v{VERSION}")
    sys.exit(0)

import asyncio
import os
import logging
import re

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ChatMemberHandler, CallbackQueryHandler, filters, ContextTypes

from agent_bot.config.settings import TELEGRAM_BOT_TOKEN, DATABASE_URL, LOG_LEVEL, INACTIVITY_ENABLED
from agent_bot.bot.telegram_handler import BettingHandler, BETTING
from agent_bot.db.storage import BettingStorage
from agent_bot.core.event_service import EventService
from agent_bot.bot.commands.command_registry import CommandRegistry
from agent_bot.bot.commands.start_command import StartCommand
from agent_bot.bot.commands.help_command import HelpCommand
from agent_bot.bot.commands.out_command import OutCommand
from agent_bot.bot.commands.status_command import StatusCommand
from agent_bot.bot.commands.transactions_command import TransactionsCommand
from agent_bot.bot.commands.undo_command import UndoCommand
from agent_bot.bot.commands.reset_command import ResetCommand
from agent_bot.bot.commands.version_command import VersionCommand
from agent_bot.bot.personality.llm_persona_service import LLMPersonalityService
from agent_bot.config.settings import PERSONALITY_ENABLED
from agent_bot.bot.services.inactivity_monitor import InactivityMonitor

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Start the Telegram bot."""
    logger.info("Starting Poker Bot...")

    # Initialize storage
    storage = BettingStorage(DATABASE_URL)

    # Initialize EventService with state machine architecture
    event_service = EventService(storage)

    # Initialize personality (LLM-based)
    personality = LLMPersonalityService() if PERSONALITY_ENABLED else None

    # Create command registry
    command_registry = CommandRegistry()
    command_registry.register("str", StartCommand(event_service, personality))
    command_registry.register("h", HelpCommand(event_service, personality))
    command_registry.register("out", OutCommand(event_service, personality))
    command_registry.register("s", StatusCommand(event_service))
    command_registry.register("t", TransactionsCommand(event_service))
    command_registry.register("u", UndoCommand(event_service))
    command_registry.register("r", ResetCommand(event_service))
    command_registry.register("v", VersionCommand())

    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Initialize inactivity monitor
    inactivity_monitor = None
    if INACTIVITY_ENABLED:
        inactivity_monitor = InactivityMonitor(application.bot, personality, storage)

    # Initialize handlers
    betting_handler = BettingHandler(event_service, command_registry, personality, inactivity_monitor)

    # Register command handlers
    application.add_handler(CommandHandler("str", betting_handler.start))
    application.add_handler(CommandHandler("h", betting_handler.help))
    application.add_handler(CommandHandler("out", betting_handler.out))
    application.add_handler(CommandHandler("s", betting_handler.status))
    application.add_handler(CommandHandler("t", betting_handler.transactions))
    application.add_handler(CommandHandler("u", betting_handler.undo))
    application.add_handler(CommandHandler("r", betting_handler.reset))

    # Register message handlers for text commands without slash (case-insensitive)
    # These must be registered BEFORE the numeric handler to take precedence
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(r'(?i)^str\b'), betting_handler.start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(r'(?i)^h\b'), betting_handler.help))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(r'(?i)^out\b'), betting_handler.out))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(r'(?i)^s\b'), betting_handler.status))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(r'(?i)^t\b'), betting_handler.transactions))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(r'(?i)^v\b'), betting_handler.version))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(r'(?i)^u\b'), betting_handler.undo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(r'(?i)^r\b'), betting_handler.reset))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, betting_handler.handle_numeric_message))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, betting_handler.new_chat_members))
    application.add_handler(ChatMemberHandler(betting_handler.chat_member))

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
