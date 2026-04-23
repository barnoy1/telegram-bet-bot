"""Undo command handler."""

from telegram import Update
from telegram.ext import ContextTypes
from agent_bot.bot.interfaces.command_handler import ICommandHandler

# Conversation state
BETTING = 0


class UndoCommand(ICommandHandler):
    """Handler for the undo command."""

    def __init__(self, event_service):
        self.event_service = event_service

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle undo command - remove last bet."""
        if not update.message or not update.message.chat:
            return BETTING

        group_id = update.message.chat.id

        # Undo last bet via EventService
        success, message = self.event_service.undo_last_bet(group_id)
        if success:
            await update.message.reply_text(f"✅ {message}", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"❌ {message}", parse_mode="Markdown")

        return BETTING
