"""Telegram bot handlers facade for betting group commands."""

import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from agent_bot.core.event_service import EventService
from agent_bot.bot.commands.command_registry import CommandRegistry
from agent_bot.bot.personality.bookie_personality import BookiePersonality
from agent_bot.bot.services.inactivity_monitor import InactivityMonitor
from agent_bot.bot.services.language_service import LanguageService
from agent_bot.bot.handlers import CommandHandler, GroupHandler, LanguageHandler, BetHandler

logger = logging.getLogger(__name__)

BETTING = 0


class BettingHandler:
    """Facade for Telegram handlers using specialized handler classes."""

    def __init__(
        self,
        event_service: EventService,
        command_registry: CommandRegistry,
        personality: BookiePersonality = None,
        inactivity_monitor: InactivityMonitor = None,
        language_service: LanguageService = None
    ):
        self.event_service = event_service
        self.command_registry = command_registry
        self.personality = personality or BookiePersonality()
        self.inactivity_monitor = inactivity_monitor
        self.language_service = language_service

        # Initialize specialized handlers
        self.command_handler = CommandHandler(
            command_registry,
            self._update_activity
        )
        self.group_handler = GroupHandler(
            personality,
            language_service,
            event_service.storage,
            self._update_activity
        )
        self.language_handler = LanguageHandler(event_service.storage)
        self.bet_handler = BetHandler(
            event_service,
            personality,
            self._update_activity
        )

    async def handle_command(self, command: str, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Generic command handler using registry."""
        return await self.command_handler.handle_command(command, update, context)

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
        """Handle bot joining a new group."""
        await self.group_handler.new_chat_members(update, context)

    async def chat_member(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle chat member updates."""
        await self.group_handler.chat_member(update, context)

    async def handle_language_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle language selection callback."""
        await self.language_handler.handle_language_selection(update, context)

    async def handle_numeric_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle numeric messages as bets."""
        return await self.bet_handler.handle_numeric_message(update, context)

    async def _update_activity(self, group_id: int):
        """Update activity timestamp for a group."""
        if self.inactivity_monitor:
            await self.inactivity_monitor.update_activity(group_id)
        else:
            self.event_service.storage.update_event_activity(group_id)
