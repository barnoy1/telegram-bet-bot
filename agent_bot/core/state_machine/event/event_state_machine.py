"""Event state machine implementation."""

from agent_bot.core.state_machine.base import StateMachine
from agent_bot.db.storage import BettingStorage
from agent_bot.db.models import EventState
from agent_bot.core.state_machine.event.idle_state import IdleState
from agent_bot.core.state_machine.event.betting_active_state import BettingActiveState
from agent_bot.core.state_machine.event.closed_state import ClosedState


class EventStateMachine(StateMachine):
    """State machine for managing event lifecycle."""

    def __init__(self, storage: BettingStorage, event_id: int, initial_state: EventState):
        """Initialize event state machine."""
        context = {
            'storage': storage,
            'event_id': event_id
        }
        
        # Map state enum to state class
        state_map = {
            EventState.IDLE: IdleState,
            EventState.BETTING_ACTIVE: BettingActiveState,
            EventState.CLOSED: ClosedState
        }
        
        initial_state_class = state_map.get(initial_state, IdleState)
        super().__init__(initial_state_class(context))

    def emit_error(self, message: str):
        """Emit error message (will be handled by EventService)."""
        # This will be overridden or handled by the service layer
        self.context.get('error_handler', lambda msg: None)(message)

    @property
    def context(self):
        """Get context dict."""
        return self.current_state.context
