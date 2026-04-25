"""Command handler using command registry."""

import logging
from telegram import Update
from telegram.ext import ContextTypes

from agent_bot.bot.commands.command_registry import CommandRegistry

logger = logging.getLogger(__name__)

BETTING = 0


class CommandHandler:
    """Handles commands via command registry."""

    def __init__(self, command_registry: CommandRegistry, update_activity_callback):
        self.command_registry = command_registry
        self.update_activity = update_activity_callback

    async def handle_command(self, command: str, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Generic command handler using registry."""
        # Update activity timestamp
        if update.message and update.message.chat:
            await self.update_activity(update.message.chat.id)
        
        # Normalize command to lowercase
        command_lower = command.lower()
        handler = self.command_registry.get(command_lower)
        if handler:
            return await handler.handle(update, context)
        else:
            await update.message.reply_text(f"❌ Unknown command: {command}", parse_mode="Markdown")
            return BETTING
