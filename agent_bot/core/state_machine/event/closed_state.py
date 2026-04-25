"""Closed state for event state machine."""

from typing import Optional
from agent_bot.core.state_machine.base import State, Event


class ClosedState(State):
    """Event is closed - no participants left."""

    def __init__(self, context):
        super().__init__(context)
        self.storage = context['storage']
        self.event_id = context['event_id']

    def validate(self, event: Event) -> bool:
        """Validate event for CLOSED state."""
        event_type = event.event_type
        
        # Only valid events in CLOSED: START (creates new event), STATUS, TRANSACTIONS
        if event_type in ('START', 'STATUS', 'TRANSACTIONS'):
            return True
            
        return False

    def handle(self, event: Event) -> Optional[State]:
        """Handle event and return next state."""
        event_type = event.event_type
        
        if event_type == 'START':
            # START creates a new fresh event (handled by service)
            # This actually creates a new event, state stays CLOSED for old event
            return None
        
        return None

    def on_entry(self, event: Event):
        """Called when entering CLOSED state."""
        # Update event state in database
        self.storage.close_event(self.event_id)
