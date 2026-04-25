"""In game state for participant state machine."""

from typing import Optional
from agent_bot.core.state_machine.base import State, Event


class InGameState(State):
    """Participant is actively in the game with a bet."""

    def __init__(self, context):
        super().__init__(context)
        self.storage = context['storage']
        self.event_id = context['event_id']
        self.user_id = context['user_id']

    def validate(self, event: Event) -> bool:
        """Validate event for IN_GAME state."""
        event_type = event.event_type
        
        # Valid events: BET (add to existing), OUT
        if event_type in ('BET', 'OUT'):
            return True
            
        return False

    def handle(self, event: Event) -> Optional[State]:
        """Handle event and return next state."""
        event_type = event.event_type
        
        if event_type == 'OUT':
            # Participant leaves with prize
            from agent_bot.core.state_machine.participant.out_state import OutState
            return OutState(self.context)
        
        # BET adds to existing bet, stays in IN_GAME
        
        return None
