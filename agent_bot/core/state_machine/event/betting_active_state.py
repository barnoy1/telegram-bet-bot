"""Betting active state for event state machine."""

from typing import Optional
from agent_bot.core.state_machine.base import State, Event
from agent_bot.db.storage import BettingStorage
from agent_bot.db.models import EventState


class BettingActiveState(State):
    """Event is active - at least one participant has bet."""

    def __init__(self, context):
        super().__init__(context)
        self.storage = context['storage']
        self.event_id = context['event_id']

    def validate(self, event: Event) -> bool:
        """Validate event for BETTING_ACTIVE state."""
        event_type = event.event_type
        
        # Valid events in BETTING_ACTIVE: BET, OUT, STATUS, TRANSACTIONS, UNDO, RESET, CLOSE
        valid_events = {'BET', 'OUT', 'STATUS', 'TRANSACTIONS', 'UNDO', 'RESET', 'CLOSE'}
        
        if event_type in valid_events:
            return True
            
        return False

    def handle(self, event: Event) -> Optional[State]:
        """Handle event and return next state."""
        event_type = event.event_type

        if event_type == 'RESET':
            # Check if no IN_GAME participants remain - transition to IDLE
            in_game_count = self.storage.get_in_game_participant_count(self.event_id)
            if in_game_count == 0:
                from agent_bot.core.state_machine.event.idle_state import IdleState
                return IdleState(self.context)

        if event_type == 'CLOSE':
            # Check if no IN_GAME participants remain
            in_game_count = self.storage.get_in_game_participant_count(self.event_id)
            if in_game_count == 0:
                from agent_bot.core.state_machine.event.closed_state import ClosedState
                return ClosedState(self.context)

        # Other events don't change state

        return None

    def on_entry(self, event: Event):
        """Called when entering BETTING_ACTIVE state."""
        # Update event state in database
        self.storage.update_event_state(self.event_id, EventState.BETTING_ACTIVE)
