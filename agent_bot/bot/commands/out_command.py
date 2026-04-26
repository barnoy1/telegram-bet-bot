"""Out command handler."""

from decimal import Decimal
from telegram import Update
from telegram.ext import ContextTypes
from agent_bot.bot.interfaces.command_handler import ICommandHandler
from agent_bot.bot.personality.llm_persona_service import LLMPersonalityService
from agent_bot.bot.utils.user_utils import get_display_name

# Conversation state
BETTING = 0


class OutCommand(ICommandHandler):
    """Handler for the out command - thin wrapper for EventService."""

    def __init__(self, event_service, personality: LLMPersonalityService = None):
        self.event_service = event_service
        self.personality = personality

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle out command - leave game with specified amount."""
        if not update.message or not update.message.chat or not update.message.from_user:
            return BETTING

        group_id = update.message.chat.id
        user_id = update.message.from_user.id
        username = get_display_name(update.message.from_user)

        # Parse amount - try context.args first, then parse from message text
        amount_str = None
        if context.args and len(context.args) >= 1:
            amount_str = context.args[0]
        elif update.message.text:
            # Parse from message text (e.g., "out 100")
            text = update.message.text.strip()
            parts = text.split()
            if len(parts) >= 2:
                amount_str = parts[1]

        if not amount_str:
            await update.message.reply_text("❌ Usage: `out <amount>`", parse_mode="Markdown")
            return BETTING

        try:
            amount = Decimal(amount_str)
            if amount <= 0:
                raise ValueError("Amount must be positive")
        except (ValueError, Exception):
            await update.message.reply_text("❌ Invalid amount. Use a positive number.", parse_mode="Markdown")
            return BETTING

        # Get current pot for taunt
        status = self.event_service.get_status(group_id)
        total_pot = status["current_pot"] if status else Decimal("0")

        # Check for big pot taunt (using LLM) - only if pot is significant
        if self.personality and total_pot >= 500:
            try:
                taunt = await self.personality.get_out_response(username, float(amount))
                if taunt:
                    await update.message.reply_text(f"💬 {taunt}", parse_mode="Markdown")
            except Exception as e:
                logger = __import__('logging').getLogger(__name__)
                logger.warning(f"Failed to generate out taunt: {e}")

        # Set user out via EventService
        success, message = self.event_service.user_out(group_id, user_id, username, amount)

        if success:
            await update.message.reply_text(f"✅ {message}", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"❌ {message}", parse_mode="Markdown")

        return BETTING
