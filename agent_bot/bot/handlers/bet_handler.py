"""Bet handler for numeric messages."""

import logging
from decimal import Decimal
from telegram import Update
from telegram.ext import ContextTypes

from agent_bot.core.event_service import EventService
from agent_bot.bot.utils.user_utils import get_display_name
from agent_bot.bot.personality.bookie_personality import BookiePersonality

logger = logging.getLogger(__name__)

BETTING = 0


class BetHandler:
    """Handles numeric messages as bets."""

    def __init__(
        self,
        event_service: EventService,
        personality: BookiePersonality = None,
        update_activity_callback=None
    ):
        self.event_service = event_service
        self.personality = personality or BookiePersonality()
        self.update_activity = update_activity_callback

    async def handle_numeric_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle numeric messages as bets without command prefix."""
        logger.info(f"handle_numeric_message called with text: {update.message.text if update.message else 'None'}")
        
        if not update.message or not update.message.chat or not update.message.from_user:
            logger.warning("Missing required fields in update")
            return BETTING

        group_id = update.message.chat.id
        user_id = update.message.from_user.id
        username = get_display_name(update.message.from_user)
        text = update.message.text.strip()

        logger.info(f"Processing numeric message: group_id={group_id}, user_id={user_id}, text={text}")
        
        # Check if this is a command without / prefix
        text_lower = text.lower()
        command_map = {
            'str': 'str',
            'h': 'h',
            'out': 'out',
            's': 's',
            'l': 'l',
            't': 't',
            'u': 'u',
            'r': 'r',
            'v': 'v',
        }
        
        for cmd in command_map.values():
            if text_lower == cmd or text_lower.startswith(cmd + ' '):
                logger.info(f"Detected command without / prefix: {text}")
                # Return without handling - let command handler deal with it
                return BETTING

        # Check if message is a valid number
        try:
            amount = Decimal(text)
            if amount <= 0:
                logger.info(f"Ignoring non-positive amount: {amount}")
                return BETTING
        except (ValueError, Exception) as e:
            logger.warning(f"Not a valid number: {text}, error: {e}")
            return BETTING

        # Check if event exists
        if not self.event_service.storage.get_event(group_id):
            logger.warning(f"Event not initialized: {group_id}")
            await update.message.reply_text(
                "❌ Event not initialized. Please run `str` first.",
                parse_mode="Markdown",
            )
            return BETTING

        logger.info(f"Adding bet: event_id={group_id}, user_id={user_id}, username={username}, amount={amount}")

        # Update activity timestamp
        if self.update_activity:
            await self.update_activity(group_id)

        # Add bet via EventService
        try:
            success, message, is_rebuy, is_adding = self.event_service.place_bet(group_id, user_id, username, amount)
            if success:
                logger.info(f"Bet placed successfully: {username} ${amount:.2f}")
                await update.message.reply_text(
                    f"✅ {message}",
                    parse_mode="Markdown",
                )

                # Send rebuy taunt if applicable
                if is_rebuy:
                    taunt = self.personality.get_rebuy_taunt(username)
                    if taunt:
                        await update.message.reply_text(f"💬 {taunt}", parse_mode="Markdown")
                # Send action taunt for adding to bet
                elif is_adding:
                    taunt = self.personality.get_bet_reaction(float(amount))
                    if taunt:
                        await update.message.reply_text(f"💬 {taunt}", parse_mode="Markdown")
            else:
                logger.error(f"Failed to record bet for {username}: {message}")
                await update.message.reply_text(f"❌ {message}", parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error adding bet: {e}", exc_info=True)
            await update.message.reply_text("❌ Error placing bet.", parse_mode="Markdown")

        return BETTING
