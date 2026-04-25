"""Not joined state for participant state machine."""

from typing import Optional
from agent_bot.core.state_machine.base import State, Event


class NotJoinedState(State):
    """Participant has not joined the event yet."""

    def __init__(self, context):
        super().__init__(context)
        self.storage = context['storage']
        self.event_id = context['event_id']
        self.user_id = context['user_id']

    def validate(self, event: Event) -> bool:
        """Validate event for NOT_JOINED state."""
        event_type = event.event_type
        
        # Only valid event: BET (to join the game)
        if event_type == 'BET':
            return True
            
        return False

    def handle(self, event: Event) -> Optional[State]:
        """Handle event and return next state."""
        event_type = event.event_type
        
        if event_type == 'BET':
            # First bet transitions to IN_GAME
            from agent_bot.core.state_machine.participant.in_game_state import InGameState
            return InGameState(self.context)
        
        return None
