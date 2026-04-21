"""Telegram bot handlers for betting group commands."""

import logging
from decimal import Decimal
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from bot.services.betting_service import BettingService
from bot.commands.command_registry import CommandRegistry
from bot.utils.user_utils import get_display_name
from bot.formatters.message_formatter import MessageFormatter
from bot.personality.bookie_personality import BookiePersonality
from bot.services.inactivity_monitor import InactivityMonitor
from datetime import datetime

logger = logging.getLogger(__name__)

# Conversation states
BETTING = 0


class BettingHandler:
    """Handles Telegram commands for betting bot using command registry."""

    def __init__(self, betting_service: BettingService, command_registry: CommandRegistry, personality: BookiePersonality = None, inactivity_monitor: InactivityMonitor = None):
        self.betting_service = betting_service
        self.command_registry = command_registry
        self.personality = personality or BookiePersonality()
        self.inactivity_monitor = inactivity_monitor

    async def handle_command(self, command: str, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Generic command handler using registry.
        
        Args:
            command: Command name (e.g., 'b', 'w', 's')
            update: Telegram update object
            context: Telegram context object
            
        Returns:
            Conversation state
        """
        # Update activity timestamp
        if update.message and update.message.chat:
            await self._update_activity(update.message.chat.id)
        
        # Normalize command to lowercase for case-insensitive matching
        command_lower = command.lower()
        handler = self.command_registry.get(command_lower)
        if handler:
            return await handler.handle(update, context)
        else:
            await update.message.reply_text(f"❌ Unknown command: {command}", parse_mode="Markdown")
            return BETTING

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle str command."""
        return await self.handle_command("str", update, context)

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle h command."""
        return await self.handle_command("h", update, context)

    async def out(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle out command."""
        return await self.handle_command("out", update, context)

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle sts command."""
        return await self.handle_command("sts", update, context)

    async def transactions(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle t command."""
        return await self.handle_command("t", update, context)

    async def undo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle u command."""
        return await self.handle_command("u", update, context)

    async def reset(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle r command."""
        return await self.handle_command("r", update, context)

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
                
                await update.message.reply_text(
                    MessageFormatter.format_welcome_message(),
                    parse_mode="Markdown",
                )
                
                # Update activity timestamp
                await self._update_activity(group_id)
                break

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
        
        # Check if this is a command without / prefix (for case-insensitive support)
        text_lower = text.lower()
        # Check for commands with potential arguments (e.g., "out 60")
        command_map = {
            'str': self.start,
            'h': self.help,
            'out': self.out,
            'sts': self.status,
            't': self.transactions,
            'u': self.undo,
            'r': self.reset,
        }
        
        for cmd, handler in command_map.items():
            if text_lower == cmd or text_lower.startswith(cmd + ' '):
                logger.info(f"Detected command without / prefix: {text}")
                # Parse arguments for commands that need them
                if text_lower.startswith(cmd + ' '):
                    # Set context.args for the handler
                    parts = text[len(cmd):].strip().split()
                    context.args = parts
                return await handler(update, context)

        # Check if message is a valid number
        try:
            amount = Decimal(text)
            if amount <= 0:
                logger.info(f"Ignoring non-positive amount: {amount}")
                return BETTING  # Ignore zero or negative numbers
        except (ValueError, Exception) as e:
            logger.warning(f"Not a valid number: {text}, error: {e}")
            return BETTING  # Not a number, ignore

        # Check if group exists
        if not self.betting_service.group_service.storage.get_group(group_id):
            logger.warning(f"Group not initialized: {group_id}")
            await update.message.reply_text(
                "❌ Group not initialized. Please run `str` first.",
                parse_mode="Markdown",
            )
            return BETTING

        logger.info(f"Adding bet: group_id={group_id}, user_id={user_id}, username={username}, amount={amount}")

        # Update activity timestamp
        await self._update_activity(group_id)

        # Add bet
        try:
            success, is_rebuy = await self.betting_service.add_bet(group_id, user_id, username, amount)
            if success:
                logger.info(f"Bet placed successfully: {username} ${amount:.2f}")
                await update.message.reply_text(
                    f"✅ {username} placed a bet of ${amount:.2f}",
                    parse_mode="Markdown",
                )
                
                # Send rebuy taunt if applicable
                if is_rebuy:
                    taunt = self.personality.get_rebuy_taunt(username)
                    if taunt:
                        await update.message.reply_text(f"💬 {taunt}", parse_mode="Markdown")
            else:
                logger.error(f"Failed to record bet for {username}")
                await update.message.reply_text("❌ Failed to record bet.", parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error adding bet: {e}", exc_info=True)
            await update.message.reply_text("❌ Error placing bet.", parse_mode="Markdown")

        return BETTING

    async def _update_activity(self, group_id: int):
        """Update activity timestamp for a group.
        
        Args:
            group_id: Telegram group ID
        """
        if self.inactivity_monitor:
            await self.inactivity_monitor.update_activity(group_id)
        else:
            # Fallback: update directly in storage
            self.betting_service.group_service.storage.update_group_activity(group_id, datetime.utcnow())
