"""Service for handling participant operations (going out, etc.)."""

from decimal import Decimal
from typing import Callable, Tuple
import logging

from agent_bot.db.storage import BettingStorage
from agent_bot.db.models import ParticipantState
from agent_bot.core.state_machine.event.event_state_machine import EventStateMachine
from agent_bot.core.state_machine.participant.participant_state_machine import ParticipantStateMachine
from agent_bot.core.state_machine.base import Event as StateEvent
from .taunt_service import TauntService

# Import enum values for cleaner code
NOT_JOINED, IN_GAME, OUT = ParticipantState

logger = logging.getLogger(__name__)


class ParticipantService:
    """Service for participant lifecycle operations."""

    def __init__(
        self,
        storage: BettingStorage,
        taunt_service: TauntService = None,
        error_handler: Callable[[str], None] = None,
        event_machine_getter: Callable[[int], EventStateMachine] = None,
        participant_machine_getter: Callable[[int, int], ParticipantStateMachine] = None
    ):
        self.storage = storage
        self.taunt_service = taunt_service or TauntService()
        self.error_handler = error_handler or (lambda msg: logger.error(msg))
        self._get_event_machine = event_machine_getter
        self._get_participant_machine = participant_machine_getter
        self._participant_machines = {}

    def _get_participant_machine(self, event_id: int, user_id: int) -> ParticipantStateMachine:
        """Get or create participant state machine."""
        if self._participant_machine_getter:
            return self._participant_machine_getter(event_id, user_id)
        
        cache_key = f"{event_id}_{user_id}"
        if cache_key not in self._participant_machines:
            participant = self.storage.get_participant(event_id, user_id)
            if participant:
                initial_state = ParticipantState(participant.state)
            else:
                initial_state = NOT_JOINED
            self._participant_machines[cache_key] = ParticipantStateMachine(
                self.storage, event_id, user_id, initial_state
            )
        return self._participant_machines[cache_key]

    def user_out(self, event_id: int, user_id: int, username: str, prize_amount: Decimal) -> Tuple[bool, str]:
        """Mark a user as OUT with prize amount."""
        try:
            # Validate amount
            if prize_amount <= 0:
                return False, "Amount must be positive"

            # Get event
            event = self.storage.get_event(event_id)
            if not event:
                return False, "Event not found"

            # Check if event is closed
            if event.state.name == "CLOSED":
                return False, "Event is closed"

            # Get participant
            participant = self.storage.get_participant(event_id, user_id)
            if not participant:
                return False, "Participant not found in event"

            if participant.state != IN_GAME:
                return False, "Participant is not in game"

            # Validate against current pot
            current_pot = self.storage.get_current_pot(event_id)
            if prize_amount > current_pot:
                return False, f"Amount exceeds current pot (${current_pot:.2f})"

            # Get event machine
            event_machine = self._get_event_machine(event_id) if self._get_event_machine else None

            # Validate event state accepts OUT
            if event_machine:
                out_event = StateEvent('OUT', {'user_id': user_id, 'amount': prize_amount})
                if not event_machine.current_state.validate(out_event):
                    return False, f"Cannot go OUT in {event_machine.state_name} state"

            # Get participant machine
            participant_machine = self._get_participant_machine(event_id, user_id)

            # Validate participant state accepts OUT
            out_event = StateEvent('OUT', {'user_id': user_id, 'amount': prize_amount})
            if not participant_machine.current_state.validate(out_event):
                return False, f"Cannot go OUT in participant {participant_machine.state_name} state"

            # Set participant as OUT
            self.storage.set_participant_out(event_id, user_id, prize_amount)

            # Calculate balance for taunt
            balance = prize_amount - participant.total_bet_amount

            # Generate taunting message
            taunt = self.taunt_service.generate_out_taunt(username, balance, prize_amount)

            # Transition participant state machine
            participant_machine.transition(out_event)

            # Transition event state machine
            if event_machine:
                event_machine.transition(out_event)

            # Check if event should close (no IN_GAME participants)
            if event_machine:
                close_event = StateEvent('CLOSE', {})
                event_machine.transition(close_event)

            # Update activity
            self.storage.update_event_activity(event_id)

            logger.info(f"User {username} went OUT with ${prize_amount:.2f} in event {event_id}")
            return True, taunt

        except Exception as e:
            error_msg = f"Failed to mark user as OUT: {e}"
            self.error_handler(error_msg)
            return False, error_msg
