"""Reset command handler."""

from telegram import Update
from telegram.ext import ContextTypes
from agent_bot.bot.interfaces.command_handler import ICommandHandler

# Conversation state
BETTING = 0


class ResetCommand(ICommandHandler):
    """Handler for the reset command."""

    def __init__(self, event_service):
        self.event_service = event_service

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle reset command - reset all bets."""
        if not update.message or not update.message.chat:
            return BETTING

        group_id = update.message.chat.id

        # Reset event via EventService
        success, message = self.event_service.reset_event(group_id)
        if success:
            await update.message.reply_text(f"✅ {message}", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"❌ {message}", parse_mode="Markdown")

        return BETTING
