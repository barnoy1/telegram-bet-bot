"""Out state for participant state machine."""

from typing import Optional
from agent_bot.core.state_machine.base import State, Event


class OutState(State):
    """Participant has left the game with a prize."""

    def __init__(self, context):
        super().__init__(context)
        self.storage = context['storage']
        self.event_id = context['event_id']
        self.user_id = context['user_id']

    def validate(self, event: Event) -> bool:
        """Validate event for OUT state."""
        event_type = event.event_type
        
        # Only valid event: BET (rebuy)
        if event_type == 'BET':
            return True
            
        return False

    def handle(self, event: Event) -> Optional[State]:
        """Handle event and return next state."""
        event_type = event.event_type
        
        if event_type == 'BET':
            # Rebuy - transitions back to IN_GAME
            from agent_bot.core.state_machine.participant.in_game_state import InGameState
            return InGameState(self.context)
        
        return None
