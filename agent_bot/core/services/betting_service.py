"""Service for handling bet placement operations."""

from decimal import Decimal
from typing import Callable, Tuple
from dataclasses import dataclass
import logging

from agent_bot.db.storage import BettingStorage
from agent_bot.db.models import ParticipantState
from agent_bot.core.state_machine.event.event_state_machine import EventStateMachine
from agent_bot.core.state_machine.participant.participant_state_machine import ParticipantStateMachine
from agent_bot.core.state_machine.base import Event as StateEvent

# Import enum values for cleaner code
NOT_JOINED, IN_GAME, OUT = ParticipantState


@dataclass
class BetResult:
    """Result of a bet placement operation."""
    success: bool
    message: str
    is_rebuy: bool
    is_adding: bool
    is_first_time: bool
    prize_amount_before: Decimal = Decimal("0")  # Prize amount before bet
    prize_amount_after: Decimal = Decimal("0")   # Prize amount after bet

logger = logging.getLogger(__name__)


class BettingService:
    """Service for bet placement and management."""

    def __init__(
        self,
        storage: BettingStorage,
        error_handler: Callable[[str], None] = None,
        event_machine_getter: Callable[[int], EventStateMachine] = None,
        participant_machine_getter: Callable[[int, int], ParticipantStateMachine] = None
    ):
        self.storage = storage
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

    def place_bet(self, event_id: int, user_id: int, username: str, amount: Decimal) -> BetResult:
        """Place a bet for a user in an event."""
        try:
            # Validate amount
            if amount <= 0:
                return BetResult(False, "Amount must be positive", False, False, False)

            # Get or create user (ensures username is up to date)
            self.storage.get_or_create_user(user_id, username)

            # Get event
            event = self.storage.get_event(event_id)
            if not event:
                return BetResult(False, "Event not found", False, False, False)

            # Check if event is closed
            if event.state.name == "CLOSED":
                return BetResult(False, "Event is closed", False, False, False)

            # Get participant
            participant = self.storage.get_participant(event_id, user_id)

            # Get event machine
            event_machine = self._get_event_machine(event_id) if self._get_event_machine else None

            # Validate event state accepts BET
            if event_machine:
                bet_event = StateEvent('BET', {'user_id': user_id, 'amount': amount})
                if not event_machine.current_state.validate(bet_event):
                    return BetResult(False, f"Cannot bet in {event_machine.state_name} state", False, False, False)

            # Get participant machine
            participant_machine = self._get_participant_machine(event_id, user_id)

            # Validate participant state accepts BET
            bet_event = StateEvent('BET', {'user_id': user_id, 'amount': amount})
            if not participant_machine.current_state.validate(bet_event):
                return BetResult(False, f"Cannot bet in participant {participant_machine.state_name} state", False, False, False)

            # Store previous state for rebuy/adding detection
            previous_state = participant_machine.current_state

            # Handle bet placement
            is_first_time = participant is None
            prize_before = participant.prize_amount if participant else Decimal("0")
            if participant is None:
                # New participant
                self.storage.create_participant(event_id, user_id, amount)
                participant = self.storage.get_participant(event_id, user_id)
            else:
                # Existing participant
                if participant.state == OUT:
                    # Rebuy - reset current_bet_amount to new amount, add to total_bet_amount
                    self.storage.rebuy_participant(event_id, user_id, amount)
                    self.storage.increment_rebuy_count(event_id, user_id)
                else:
                    # Adding to existing bet
                    self.storage.update_participant_bet(event_id, user_id, amount)

            # Get updated participant to check prize after
            participant_after = self.storage.get_participant(event_id, user_id)
            prize_after = participant_after.prize_amount if participant_after else Decimal("0")

            # Transition participant state machine
            participant_machine.transition(bet_event)

            # Check for rebuy or adding to bet
            is_rebuy = participant_machine.is_rebuy(previous_state)
            is_adding = participant_machine.is_adding_to_bet(previous_state)

            # Transition event state machine
            if event_machine:
                event_machine.transition(bet_event)

            # Update activity
            self.storage.update_event_activity(event_id)

            logger.info(f"Bet placed: {username} ${amount:.2f} in event {event_id}")
            return BetResult(True, f"Bet placed: ${amount:.2f}", is_rebuy, is_adding, is_first_time, prize_before, prize_after)

        except Exception as e:
            error_msg = f"Failed to place bet: {e}"
            self.error_handler(error_msg)
            return BetResult(False, error_msg, False, False, False, Decimal("0"), Decimal("0"))
