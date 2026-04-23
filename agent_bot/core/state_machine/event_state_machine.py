"""Event state machine implementation (IDLE, BETTING_ACTIVE, CLOSED)."""

from typing import Optional
from agent_bot.core.state_machine.base import State, StateMachine, Event
from agent_bot.db.storage import BettingStorage
from agent_bot.db.models import EventState


class IdleState(State):
    """Event is idle - no bets placed yet."""

    def __init__(self, context):
        super().__init__(context)
        self.storage = context['storage']

    def validate(self, event: Event) -> bool:
        """Validate event for IDLE state."""
        event_type = event.event_type
        
        # Valid events in IDLE: START, BET
        if event_type in ('START', 'BET'):
            return True
        
        # STATUS and TRANSACTIONS are always valid (read-only)
        if event_type in ('STATUS', 'TRANSACTIONS'):
            return True
            
        return False

    def handle(self, event: Event) -> Optional[State]:
        """Handle event and return next state."""
        event_type = event.event_type
        
        if event_type == 'BET':
            # First bet transitions to BETTING_ACTIVE
            return BettingActiveState(self.context)
        
        # START creates a fresh event (handled by service, state stays IDLE)
        # STATUS, TRANSACTIONS are stateless queries
        
        return None


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
        
        if event_type == 'CLOSE':
            # Check if no IN_GAME participants remain
            in_game_count = self.storage.get_in_game_participant_count(self.event_id)
            if in_game_count == 0:
                return ClosedState(self.context)
        
        # Other events don't change state
        
        return None

    def on_entry(self, event: Event):
        """Called when entering BETTING_ACTIVE state."""
        # Update event state in database
        self.storage.update_event_state(self.event_id, EventState.BETTING_ACTIVE)


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
