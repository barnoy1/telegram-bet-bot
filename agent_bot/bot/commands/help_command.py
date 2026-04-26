"""Help command handler."""

from telegram import Update
from telegram.ext import ContextTypes
from agent_bot.bot.interfaces.command_handler import ICommandHandler
from agent_bot.bot.formatters.message_formatter import MessageFormatter
from agent_bot.bot.personality.llm_persona_service import LLMPersonalityService


class HelpCommand(ICommandHandler):
    """Handler for the help command."""

    def __init__(self, event_service, personality: LLMPersonalityService = None):
        self.event_service = event_service
        self.personality = personality

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle help command."""
        if not update.message or not update.message.chat:
            return 0

        message_formatter = MessageFormatter(self.personality)

        await update.message.reply_text(
            message_formatter.format_help_message(),
            parse_mode="Markdown",
        )
        return 0
