"""Group event handlers (new members, chat member updates)."""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from agent_bot.bot.formatters.message_formatter import MessageFormatter
from agent_bot.bot.personality.bookie_personality import BookiePersonality
from agent_bot.bot.services.language_service import LanguageService

logger = logging.getLogger(__name__)


class GroupHandler:
    """Handles group-related events."""

    def __init__(
        self,
        personality: BookiePersonality = None,
        language_service: LanguageService = None,
        storage=None,
        update_activity_callback=None
    ):
        self.personality = personality or BookiePersonality()
        self.language_service = language_service
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

                # Create formatter with language service
                message_formatter = MessageFormatter(self.personality, self.language_service, group_id)

                await update.message.reply_text(
                    message_formatter.format_welcome_message(),
                    parse_mode="Markdown",
                )

                # Update activity timestamp
                if self.update_activity:
                    await self.update_activity(group_id)
                break

    async def chat_member(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle chat member updates to track languages when users join."""
        if not update.chat_member:
            return

        # Track language when a user joins the group
        new_member = update.chat_member.new_chat_member
        old_member = update.chat_member.old_chat_member

        # Check if user joined (was not a member before, is now)
        if old_member.status in ['left', 'kicked'] and new_member.status in ['member', 'administrator']:
            group_id = update.chat_member.chat.id
            user_id = new_member.user.id
            language_code = new_member.user.language_code or 'en'

            # Track language in database
            try:
                if self.storage:
                    self.storage.increment_language(group_id, language_code)
                    logger.info(f"Tracked language {language_code} for user {user_id} in group {group_id}")
            except Exception as e:
                logger.error(f"Failed to track language: {e}")

            # If administrator joined, ask for language selection
            if new_member.status == 'administrator':
                await self._prompt_language_selection(update, group_id)

    async def _prompt_language_selection(self, update: Update, group_id: int) -> None:
        """Prompt administrator to select language for the group."""
        keyboard = [
            [
                InlineKeyboardButton("🇬🇧 English", callback_data=f"lang_en_{group_id}"),
                InlineKeyboardButton("🇮🇱 עברית", callback_data=f"lang_he_{group_id}"),
                InlineKeyboardButton("🇷🇺 Русский", callback_data=f"lang_ru_{group_id}"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = (
            "🌐 **Choose Language / בחר שפה / Выберите язык**\n\n"
            "Select the language for this group:\n"
            "בחר את השפה עבור הקבוצה:\n"
            "Выберите язык для этой группы:"
        )
        
        await update.chat_member.chat.send_message(message, reply_markup=reply_markup, parse_mode="Markdown")
