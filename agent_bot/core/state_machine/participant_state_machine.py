"""Participant state machine implementation (NOT_JOINED, IN_GAME, OUT)."""

from typing import Optional
from agent_bot.core.state_machine.base import State, StateMachine, Event
from agent_bot.db.storage import BettingStorage
from agent_bot.db.models import ParticipantState
from decimal import Decimal

# Import enum values for cleaner code
NOT_JOINED, IN_GAME, OUT = ParticipantState


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
            return InGameState(self.context)
        
        return None


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
            return OutState(self.context)
        
        # BET adds to existing bet, stays in IN_GAME
        
        return None


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
            return InGameState(self.context)
        
        return None


class ParticipantStateMachine(StateMachine):
    """State machine for managing participant lifecycle."""

    def __init__(self, storage: BettingStorage, event_id: int, user_id: int, initial_state: ParticipantState):
        """Initialize participant state machine."""
        context = {
            'storage': storage,
            'event_id': event_id,
            'user_id': user_id
        }
        
        # Map state enum to state class
        state_map = {
            NOT_JOINED: NotJoinedState,
            IN_GAME: InGameState,
            OUT: OutState
        }
        
        initial_state_class = state_map.get(initial_state, NotJoinedState)
        super().__init__(initial_state_class(context))

    def emit_error(self, message: str):
        """Emit error message (will be handled by EventService)."""
        # This will be overridden or handled by the service layer
        self.context.get('error_handler', lambda msg: None)(message)

    @property
    def context(self):
        """Get context dict."""
        return self.current_state.context

    def is_rebuy(self, previous_state: State) -> bool:
        """Check if this transition is a rebuy (OUT -> IN_GAME)."""
        return isinstance(previous_state, OutState) and isinstance(self.current_state, InGameState)

    def is_adding_to_bet(self, previous_state: State) -> bool:
        """Check if this is adding to existing bet (IN_GAME -> IN_GAME)."""
        return isinstance(previous_state, InGameState) and isinstance(self.current_state, InGameState)
