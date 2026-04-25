"""Participant state machine implementation."""

from agent_bot.core.state_machine.base import StateMachine, State
from agent_bot.db.storage import BettingStorage
from agent_bot.db.models import ParticipantState
from agent_bot.core.state_machine.participant.not_joined_state import NotJoinedState
from agent_bot.core.state_machine.participant.in_game_state import InGameState
from agent_bot.core.state_machine.participant.out_state import OutState

# Import enum values for cleaner code
NOT_JOINED, IN_GAME, OUT = ParticipantState


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
