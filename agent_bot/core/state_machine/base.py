"""Base classes for state machine implementation (Moore pattern)."""

from abc import ABC, abstractmethod
from typing import Optional, Any
from dataclasses import dataclass


@dataclass
class Event:
    """Base event class for state machine transitions."""
    event_type: str
    data: dict = None

    def __post_init__(self):
        if self.data is None:
            self.data = {}


class State(ABC):
    """Base state class for Moore state machine pattern."""

    def __init__(self, context: Any = None):
        self.context = context

    @abstractmethod
    def handle(self, event: Event) -> Optional['State']:
        """
        Handle an event and return the next state.
        
        Args:
            event: The event to handle
            
        Returns:
            Next state instance, or None to stay in current state
        """
        pass

    @abstractmethod
    def validate(self, event: Event) -> bool:
        """
        Validate if the event can be handled in this state.
        
        Args:
            event: The event to validate
            
        Returns:
            True if event is valid for this state
        """
        pass

    def on_entry(self, event: Event):
        """Called when entering this state."""
        pass

    def on_exit(self, event: Event):
        """Called when exiting this state."""
        pass

    def __repr__(self):
        return f"{self.__class__.__name__}"


class StateMachine(ABC):
    """Base state machine class."""

    def __init__(self, initial_state: State):
        self.current_state = initial_state
        self.current_state.on_entry(Event("INIT"))

    def transition(self, event: Event) -> bool:
        """
        Process an event and transition to next state if valid.
        
        Args:
            event: The event to process
            
        Returns:
            True if transition occurred, False otherwise
        """
        if not self.current_state.validate(event):
            return False

        next_state = self.current_state.handle(event)
        
        if next_state and next_state != self.current_state:
            self.current_state.on_exit(event)
            self.current_state = next_state
            self.current_state.on_entry(event)
            return True
        
        return False

    @property
    def state_name(self) -> str:
        """Get the name of the current state."""
        return self.current_state.__class__.__name__

    def emit_error(self, message: str):
        """Emit an error message (to be overridden by subclasses)."""
        pass
