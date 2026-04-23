"""Language command handler."""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from agent_bot.bot.interfaces.command_handler import ICommandHandler
from agent_bot.bot.services.language_service import LanguageService

# Conversation state
BETTING = 0


class LanguageCommand(ICommandHandler):
    """Handler for the language command - allows manual language selection."""

    def __init__(self, language_service: LanguageService):
        self.language_service = language_service

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle language command."""
        if not update.message or not update.message.chat:
            return ConversationHandler.END

        group_id = update.message.chat.id

        # Create language selection inline keyboard
        keyboard = [
            [
                InlineKeyboardButton("🇬🇧 English", callback_data=f"lang_en_{group_id}"),
                InlineKeyboardButton("🇮🇱 עברית", callback_data=f"lang_he_{group_id}"),
                InlineKeyboardButton("🇷🇺 Русский", callback_data=f"lang_ru_{group_id}"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "🌐 Choose language / בחר שפה / Выберите язык:",
            reply_markup=reply_markup,
        )
        return BETTING
