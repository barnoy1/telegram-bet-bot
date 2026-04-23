"""Version command handler."""

from telegram import Update
from telegram.ext import ContextTypes
from agent_bot.bot.interfaces.command_handler import ICommandHandler
from agent_bot.config.settings import VERSION


class VersionCommand(ICommandHandler):
    """Handler for the version command."""

    def __init__(self, event_service=None, personality=None):
        self.event_service = event_service
        self.personality = personality

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle version command."""
        await update.message.reply_text(f"Poker Bot v{VERSION}")
        return 0
