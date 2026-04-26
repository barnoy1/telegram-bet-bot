"""Start command handler."""

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from agent_bot.bot.interfaces.command_handler import ICommandHandler
from agent_bot.bot.formatters.message_formatter import MessageFormatter
from agent_bot.bot.personality.llm_persona_service import LLMPersonalityService
from agent_bot.bot.utils.user_utils import get_display_name

# Conversation state
BETTING = 0


class StartCommand(ICommandHandler):
    """Handler for the start command - thin wrapper for EventService."""

    def __init__(self, event_service, personality: LLMPersonalityService = None):
        self.event_service = event_service
        self.personality = personality

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle start command."""
        if not update.message or not update.message.chat:
            return ConversationHandler.END

        group_id = update.message.chat.id
        chat_title = update.message.chat.title or f"Group {group_id}"
        user_id = update.message.from_user.id
        username = get_display_name(update.message.from_user)

        # Start event via EventService
        success, message = self.event_service.start_event(group_id, chat_title, user_id, username)

        # Create formatter (English only)
        message_formatter = MessageFormatter(self.personality)

        await update.message.reply_text(
            message if not success else message_formatter.format_start_message(),
            parse_mode="Markdown",
        )
        return BETTING
