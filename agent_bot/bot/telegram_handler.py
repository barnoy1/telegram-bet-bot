"""Telegram bot handlers for betting group commands."""

import logging
from decimal import Decimal
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from agent_bot.core.event_service import EventService
from agent_bot.bot.commands.command_registry import CommandRegistry
from agent_bot.bot.utils.user_utils import get_display_name
from agent_bot.bot.formatters.message_formatter import MessageFormatter
from agent_bot.bot.personality.bookie_personality import BookiePersonality
from agent_bot.bot.services.inactivity_monitor import InactivityMonitor
from agent_bot.bot.services.language_service import LanguageService

logger = logging.getLogger(__name__)

# Conversation states
BETTING = 0


class BettingHandler:
    """Handles Telegram commands for betting bot using command registry."""

    def __init__(self, event_service: EventService, command_registry: CommandRegistry, personality: BookiePersonality = None, inactivity_monitor: InactivityMonitor = None, language_service: LanguageService = None):
        self.event_service = event_service
        self.command_registry = command_registry
        self.personality = personality or BookiePersonality()
        self.inactivity_monitor = inactivity_monitor
        self.language_service = language_service

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
        """Handle s command."""
        return await self.handle_command("s", update, context)

    async def language(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle l command."""
        return await self.handle_command("l", update, context)

    async def transactions(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle t command."""
        return await self.handle_command("t", update, context)

    async def undo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle u command."""
        return await self.handle_command("u", update, context)

    async def reset(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle r command."""
        return await self.handle_command("r", update, context)

    async def version(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle v command."""
        return await self.handle_command("v", update, context)

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
                await self._update_activity(group_id)
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
            language_code = new_member.user.language_code or 'en'  # Fallback to English

            # Track language in database
            try:
                self.event_service.storage.increment_language(group_id, language_code)
                logger.info(f"Tracked language {language_code} for user {user_id} in group {group_id}")
            except Exception as e:
                logger.error(f"Failed to track language: {e}")

            # If administrator joined, ask for language selection
            if new_member.status == 'administrator':
                await self._prompt_language_selection(update, group_id)

    async def _prompt_language_selection(self, update: Update, group_id: int) -> None:
        """Prompt administrator to select language for the group."""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
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

    async def handle_language_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle language selection callback from inline keyboard."""
        query = update.callback_query
        if not query:
            return
        
        await query.answer()
        
        # Parse callback data: lang_en_{group_id}
        callback_data = query.data
        if not callback_data.startswith("lang_"):
            return
        
        parts = callback_data.split("_")
        if len(parts) < 3:
            return
        
        lang_code = parts[1]
        group_id = int(parts[2])
        
        # Store language preference for group
        try:
            # Store in database - we need to add a method for this
            # For now, we'll use the language stats to set the dominant language
            # Increment the selected language multiple times to make it dominant
            for _ in range(100):  # Ensure it becomes the dominant language
                self.event_service.storage.increment_language(group_id, lang_code)
            
            lang_names = {
                'en': 'English',
                'he': 'עברית',
                'ru': 'Русский'
            }
            
            confirmation = f"✅ Language set to {lang_names.get(lang_code, lang_code)}"
            await query.edit_message_text(confirmation)
            logger.info(f"Group {group_id} language set to {lang_code}")
        except Exception as e:
            logger.error(f"Failed to set language for group {group_id}: {e}")
            await query.edit_message_text("❌ Failed to set language")

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
            's': self.status,
            'l': self.language,
            't': self.transactions,
            'u': self.undo,
            'r': self.reset,
            'v': self.version,
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
        await self._update_activity(group_id)

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

    async def _update_activity(self, group_id: int):
        """Update activity timestamp for a group.
        
        Args:
            group_id: Telegram group ID
        """
        if self.inactivity_monitor:
            await self.inactivity_monitor.update_activity(group_id)
        else:
            # Fallback: update directly in storage
            self.event_service.storage.update_event_activity(group_id)
