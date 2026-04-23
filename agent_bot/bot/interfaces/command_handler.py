"""Interface for command handlers."""

from abc import ABC, abstractmethod
from telegram import Update
from telegram.ext import ContextTypes


class ICommandHandler(ABC):
    """Interface for Telegram command handlers."""

    @abstractmethod
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle a command.
        
        Args:
            update: Telegram update object
            context: Telegram context object
            
        Returns:
            Conversation state
        """
        pass
