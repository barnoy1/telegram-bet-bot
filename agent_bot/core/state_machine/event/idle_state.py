"""Idle state for event state machine."""

from typing import Optional
from agent_bot.core.state_machine.base import State, Event


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
            from agent_bot.core.state_machine.event.betting_active_state import BettingActiveState
            return BettingActiveState(self.context)
        
        # START creates a fresh event (handled by service, state stays IDLE)
        # STATUS, TRANSACTIONS are stateless queries
        
        return None
