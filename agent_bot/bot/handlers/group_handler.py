"""Group event handlers (new members, chat member updates)."""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from agent_bot.bot.formatters.message_formatter import MessageFormatter
from agent_bot.bot.personality.llm_persona_service import LLMPersonalityService

logger = logging.getLogger(__name__)


class GroupHandler:
    """Handles group-related events."""

    def __init__(
        self,
        personality: LLMPersonalityService = None,
        storage=None,
        update_activity_callback=None
    ):
        self.personality = personality
        self.storage = storage
        self.update_activity = update_activity_callback

    async def new_chat_members(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle bot joining a new group - send welcome message."""
        if not update.message or not update.message.chat or not update.message.new_chat_members:
            return

        # Check if bot itself was added to the group
        bot_id = context.bot.id
        for member in update.message.new_chat_members:
            if member.id == bot_id:
                group_id = update.message.chat.id
                chat_title = update.message.chat.title or f"Group {group_id}"

                # Create formatter (English only)
                message_formatter = MessageFormatter(self.personality)

                await update.message.reply_text(
                    message_formatter.format_welcome_message(),
                    parse_mode="Markdown",
                )

                # Update activity timestamp
                if self.update_activity:
                    await self.update_activity(group_id)
                break

    async def chat_member(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle chat member updates (language tracking disabled)."""
        # Language tracking disabled - English only
        pass
