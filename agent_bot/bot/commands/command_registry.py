"""Command registry for managing command handlers."""

from typing import Dict, Optional
from agent_bot.bot.interfaces.command_handler import ICommandHandler


class CommandRegistry:
    """Registry for command handlers."""

    def __init__(self):
        self._handlers: Dict[str, ICommandHandler] = {}

    def register(self, command: str, handler: ICommandHandler) -> None:
        """Register a command handler.
        
        Args:
            command: Command name (e.g., 'b', 'w', 's')
            handler: Command handler instance
        """
        self._handlers[command] = handler

    def get(self, command: str) -> Optional[ICommandHandler]:
        """Get a command handler by command name (case-insensitive).
        
        Args:
            command: Command name
            
        Returns:
            Command handler instance or None if not found
        """
        return self._handlers.get(command.lower())

    def get_case_insensitive(self, command: str) -> Optional[ICommandHandler]:
        """Get a command handler by command name (case-insensitive alias).
        
        Args:
            command: Command name
            
        Returns:
            Command handler instance or None if not found
        """
        return self.get(command)

    def get_all(self) -> Dict[str, ICommandHandler]:
        """Get all registered command handlers.
        
        Returns:
            Dictionary of command -> handler
        """
        return self._handlers.copy()
