"""Event service facade coordinating business logic services."""

from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Callable
import logging

from agent_bot.db.storage import BettingStorage
from agent_bot.db.models import Event, Participant, EventState, ParticipantState
from agent_bot.core.state_machine.event.event_state_machine import EventStateMachine
from agent_bot.core.state_machine.participant.participant_state_machine import ParticipantStateMachine
from agent_bot.core.settlement.hungarian_settlement import HungarianSettlementService
from agent_bot.core.services import (
    EventLifecycleService,
    BettingService,
    ParticipantService,
    TauntService
)
from agent_bot.core.services.betting_service import BetResult

logger = logging.getLogger(__name__)


class EventService:
    """Facade service coordinating all business logic services."""

    def __init__(self, storage: BettingStorage, error_handler: Callable[[str], None] = None, llm_service=None):
        self.storage = storage
        self.error_handler = error_handler or (lambda msg: logger.error(msg))
        self.llm_service = llm_service  # Optional LLM service for generating responses

        # Cache for state machines
        self._event_machines: Dict[int, EventStateMachine] = {}
        self._participant_machines: Dict[str, ParticipantStateMachine] = {}

        # Initialize sub-services
        self.taunt_service = TauntService()
        self.event_lifecycle = EventLifecycleService(
            storage,
            error_handler,
            self._get_event_machine,
            self._clear_event_machine
        )
        self.betting_service = BettingService(
            storage,
            error_handler,
            self._get_event_machine,
            self._get_participant_machine
        )
        self.participant_service = ParticipantService(
            storage,
            self.taunt_service,
            llm_service,
            error_handler,
            self._get_event_machine,
            self._get_participant_machine
        )

    def _get_event_machine(self, event_id: int) -> EventStateMachine:
        """Get or create event state machine."""
        if event_id not in self._event_machines:
            event = self.storage.get_event(event_id)
            if not event:
                raise ValueError(f"Event {event_id} not found")
            initial_state = EventState(event.state)
            self._event_machines[event_id] = EventStateMachine(
                self.storage, event_id, initial_state
            )
        return self._event_machines[event_id]

    def _get_participant_machine(self, event_id: int, user_id: int) -> ParticipantStateMachine:
        """Get or create participant state machine."""
        cache_key = f"{event_id}_{user_id}"
        if cache_key not in self._participant_machines:
            participant = self.storage.get_participant(event_id, user_id)
            if participant:
                initial_state = ParticipantState(participant.state)
            else:
                initial_state = ParticipantState.NOT_JOINED
            self._participant_machines[cache_key] = ParticipantStateMachine(
                self.storage, event_id, user_id, initial_state
            )
        return self._participant_machines[cache_key]

    def _clear_event_machine(self, event_id: int):
        """Clear event state machine from cache."""
        if event_id in self._event_machines:
            del self._event_machines[event_id]
        # Also clear all participant machines for this event
        keys_to_delete = [key for key in self._participant_machines if key.startswith(f"{event_id}_")]
        for key in keys_to_delete:
            del self._participant_machines[key]

    # Delegate to EventLifecycleService
    def start_event(self, event_id: int, title: str, creator_id: int, creator_name: str) -> Tuple[bool, str]:
        """Start a new betting event."""
        return self.event_lifecycle.start_event(event_id, title, creator_id, creator_name)

    def close_event(self, event_id: int) -> Tuple[bool, str]:
        """Close an event."""
        return self.event_lifecycle.close_event(event_id)

    def reset_event(self, event_id: int) -> Tuple[bool, str]:
        """Reset an event."""
        return self.event_lifecycle.reset_event(event_id)

    def undo_last_bet(self, event_id: int) -> Tuple[bool, str]:
        """Undo the last bet in an event."""
        return self.event_lifecycle.undo_last_bet(event_id)

    # Delegate to BettingService
    def place_bet(self, event_id: int, user_id: int, username: str, amount: Decimal) -> BetResult:
        """Place a bet for a user in an event."""
        return self.betting_service.place_bet(event_id, user_id, username, amount)

    # Delegate to ParticipantService
    def user_out(self, event_id: int, user_id: int, username: str, prize_amount: Decimal) -> Tuple[bool, str]:
        """Mark a user as OUT with prize amount."""
        return self.participant_service.user_out(event_id, user_id, username, prize_amount)

    # Status and settlement methods
    def get_status(self, event_id: int) -> Optional[Dict]:
        """Get event status summary (optimized single-query version)."""
        try:
            return self.storage.get_event_status_optimized(event_id)
        except Exception as e:
            self.error_handler(f"Failed to get status: {e}")
            return None

    def get_transactions(self, event_id: int) -> List[Dict]:
        """Get settlement transactions for an event."""
        try:
            transactions = self.storage.get_transactions(event_id)
            return [
                {
                    "from_user_id": tx.from_user_id,
                    "to_user_id": tx.to_user_id,
                    "amount": tx.amount,
                    "created_at": tx.created_at
                }
                for tx in transactions
            ]
        except Exception as e:
            self.error_handler(f"Failed to get transactions: {e}")
            return []

    def calculate_settlement(self, event_id: int) -> Tuple[bool, str, List[Tuple]]:
        """Calculate settlement transactions using greedy algorithm."""
        try:
            event = self.storage.get_event(event_id)
            if not event:
                return False, "Event not found", []
            
            participants = self.storage.get_all_participants(event_id)
            
            # Calculate transactions
            transactions = HungarianSettlementService.calculate_settlement(participants)
            
            # Save transactions
            tx_dicts = [
                {
                    "from_user_id": tx[0],
                    "to_user_id": tx[1],
                    "amount": tx[2]
                }
                for tx in transactions
            ]
            self.storage.save_transactions(event_id, tx_dicts)
            
            logger.info(f"Settlement calculated for event {event_id}: {len(transactions)} transactions")
            return True, "Settlement calculated successfully", transactions
            
        except Exception as e:
            error_msg = f"Failed to calculate settlement: {e}"
            self.error_handler(error_msg)
            return False, error_msg, []
