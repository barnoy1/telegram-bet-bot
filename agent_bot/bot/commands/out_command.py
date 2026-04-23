"""Out command handler."""

from decimal import Decimal
from telegram import Update
from telegram.ext import ContextTypes
from agent_bot.bot.interfaces.command_handler import ICommandHandler
from agent_bot.bot.personality.bookie_personality import BookiePersonality
from agent_bot.bot.utils.user_utils import get_display_name

# Conversation state
BETTING = 0


class OutCommand(ICommandHandler):
    """Handler for the out command - thin wrapper for EventService."""

    def __init__(self, event_service, personality: BookiePersonality = None):
        self.event_service = event_service
        self.personality = personality or BookiePersonality()

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle out command - leave game with specified amount."""
        if not update.message or not update.message.chat or not update.message.from_user:
            return BETTING

        group_id = update.message.chat.id
        user_id = update.message.from_user.id
        username = get_display_name(update.message.from_user)

        # Parse amount
        if not context.args or len(context.args) < 1:
            await update.message.reply_text("❌ Usage: `out <amount>`", parse_mode="Markdown")
            return BETTING

        try:
            amount = Decimal(context.args[0])
            if amount <= 0:
                raise ValueError("Amount must be positive")
        except (ValueError, Exception):
            await update.message.reply_text("❌ Invalid amount. Use a positive number.", parse_mode="Markdown")
            return BETTING

        # Get current pot for taunt
        status = self.event_service.get_status(group_id)
        total_pot = status["current_pot"] if status else Decimal("0")

        # Check for big pot taunt
        taunt = self.personality.get_big_pot_out_taunt(username, total_pot)
        if taunt:
            await update.message.reply_text(f"💬 {taunt}", parse_mode="Markdown")

        # Set user out via EventService
        success, message = self.event_service.user_out(group_id, user_id, username, amount)

        if success:
            await update.message.reply_text(f"✅ {message}", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"❌ {message}", parse_mode="Markdown")

        return BETTING
