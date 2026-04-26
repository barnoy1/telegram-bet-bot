"""Bet handler for numeric messages."""

import asyncio
import logging
from decimal import Decimal
from telegram import Update
from telegram.ext import ContextTypes

from agent_bot.core.event_service import EventService
from agent_bot.bot.utils.user_utils import get_display_name
from agent_bot.bot.personality.llm_persona_service import LLMPersonalityService
from agent_bot.config.settings import BIG_POT_PERCENT

logger = logging.getLogger(__name__)

BETTING = 0


class BetHandler:
    """Handles numeric messages as bets."""

    def __init__(
        self,
        event_service: EventService,
        personality: LLMPersonalityService = None,
        update_activity_callback=None
    ):
        self.event_service = event_service
        self.personality = personality
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
            't': 't',
            'u': 'u',
            'r': 'r',
            'v': 'v',
        }
        
        for cmd in command_map.values():
            if text_lower == cmd or text_lower.startswith(cmd + ' '):
                logger.info(f"Detected command without / prefix: {text} - letting command handler process it")
                # Return without handling - let command handler deal with it
                return None

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
            result = self.event_service.place_bet(group_id, user_id, username, amount)
            if result.success:
                logger.info(f"Bet placed successfully: {username} ${amount:.2f}, is_rebuy={result.is_rebuy}, is_adding={result.is_adding}, is_first_time={result.is_first_time}")
                await update.message.reply_text(
                    f"✅ {result.message}",
                    parse_mode="Markdown",
                )

                # Check if player is taking BIG_POT_PERCENT%+ of pot for teasing response
                status = self.event_service.get_status(group_id)
                if status and status.get("current_pot"):
                    current_pot = status["current_pot"]
                    if current_pot > 0:
                        pot_percentage = (float(amount) / float(current_pot)) * 100
                        logger.info(f"Pot percentage check: {pot_percentage:.1f}%")
                        if pot_percentage >= (BIG_POT_PERCENT * 100):
                            logger.info(f"Scheduling async big takeover taunt for {username}")
                            if self.personality:
                                asyncio.create_task(self.personality.send_big_takeover_response_async(username, float(amount), pot_percentage, update, context))

                # Send new player taunt if applicable (async, non-blocking)
                if result.is_first_time:
                    logger.info(f"Scheduling async new player taunt for {username}")
                    if self.personality:
                        asyncio.create_task(self.personality.send_new_player_response_async(username, float(amount), update, context))
                # Send rebuy taunt if applicable (async, non-blocking)
                elif result.is_rebuy:
                    logger.info(f"Scheduling async rebuy taunt for {username}")
                    if self.personality:
                        # Determine which rebuy scenario based on prize amounts
                        if result.prize_amount_before > 0:
                            if result.prize_amount_after > 0:
                                # Rebuying with less than prize amount (keeping some winnings)
                                asyncio.create_task(self.personality.send_rebuy_with_prize_response_async(
                                    username, float(amount), float(result.prize_amount_after), update, context
                                ))
                            else:
                                # Rebuying with more than prize amount (using all winnings + new money)
                                asyncio.create_task(self.personality.send_rebuy_exceeding_prize_response_async(
                                    username, float(amount), float(result.prize_amount_before), update, context
                                ))
                        else:
                            # Regular rebuy with no prize money
                            asyncio.create_task(self.personality.send_rebuy_response_async(username, update, context))
                # Send action taunt for adding to bet (async, non-blocking)
                elif result.is_adding:
                    logger.info(f"Scheduling async bet taunt for {username} (adding to bet)")
                    if self.personality:
                        asyncio.create_task(self.personality.send_bet_response_async(username, float(amount), update, context))
                else:
                    logger.info(f"No taunt sent - is_rebuy={result.is_rebuy}, is_adding={result.is_adding}, is_first_time={result.is_first_time}")
            else:
                logger.error(f"Failed to record bet for {username}: {result.message}")
                await update.message.reply_text(f"❌ {result.message}", parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error adding bet: {e}", exc_info=True)
            await update.message.reply_text("❌ Error placing bet.", parse_mode="Markdown")

        return BETTING
