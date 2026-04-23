"""Status command handler."""

from telegram import Update
from telegram.ext import ContextTypes
from agent_bot.bot.interfaces.command_handler import ICommandHandler
from agent_bot.bot.formatters.status_formatter import StatusFormatter
from agent_bot.bot.services.language_service import LanguageService

# Conversation state
BETTING = 0


class StatusCommand(ICommandHandler):
    """Handler for the status command."""

    def __init__(self, event_service, language_service: LanguageService = None):
        self.event_service = event_service
        self.language_service = language_service

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle status command - show current group state."""
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Status command called for group {update.message.chat.id if update.message else 'Unknown'}")
        
        if not update.message or not update.message.chat:
            return BETTING

        group_id = update.message.chat.id

        # Get event status
        logger.info(f"Fetching status for event_id: {group_id}")
        status = self.event_service.get_status(group_id)
        logger.info(f"Status found: {status is not None}")
        
        if not status:
            await update.message.reply_text(
                "❌ Event not initialized. Please run `str` first.",
                parse_mode="Markdown",
            )
            return BETTING
        
        # Convert status to summary format for formatter
        summary = {
            "group": status["event"],
            "participants": status["participants"],
            "total_pot": status["current_pot"],
            "winners": [p for p in status["participants"] if p.state == "OUT"],
            "status": status["state"]
        }

        # Format and send status with language service
        status_formatter = StatusFormatter(self.language_service, group_id)
        status_message = status_formatter.format(summary)
        await update.message.reply_text(status_message)

        return BETTING
