"""Service for managing event lifecycle operations."""

from typing import Callable, Optional
import logging

from agent_bot.db.storage import BettingStorage
from agent_bot.db.models import EventState
from agent_bot.core.state_machine.event.event_state_machine import EventStateMachine
from agent_bot.core.state_machine.base import Event as StateEvent

logger = logging.getLogger(__name__)


class EventLifecycleService:
    """Service for event lifecycle operations (start, close, reset)."""

    def __init__(
        self,
        storage: BettingStorage,
        error_handler: Callable[[str], None] = None,
        event_machine_getter: Callable[[int], EventStateMachine] = None,
        clear_event_machine_callback: Callable[[int], None] = None
    ):
        self.storage = storage
        self.error_handler = error_handler or (lambda msg: logger.error(msg))
        self._external_event_machine_getter = event_machine_getter
        self._clear_event_machine = clear_event_machine_callback
        self._event_machines = {}

    def _get_event_machine(self, event_id: int) -> EventStateMachine:
        """Get or create event state machine."""
        if self._external_event_machine_getter:
            return self._external_event_machine_getter(event_id)
        
        if event_id not in self._event_machines:
            event = self.storage.get_event(event_id)
            if not event:
                raise ValueError(f"Event {event_id} not found")
            initial_state = EventState(event.state)
            self._event_machines[event_id] = EventStateMachine(
                self.storage, event_id, initial_state
            )
        return self._event_machines[event_id]

    def start_event(self, event_id: int, group_name: str, creator_id: int, creator_name: str) -> tuple[bool, str]:
        """Start a new betting event."""
        try:
            # Check if event already exists
            existing_event = self.storage.get_event(event_id)
            if existing_event:
                if existing_event.state == EventState.CLOSED:
                    # Delete closed event and create new one
                    self.storage.delete_event(event_id)
                    # Clear state machine cache to ensure new event starts fresh
                    if self._clear_event_machine:
                        self._clear_event_machine(event_id)
                    elif event_id in self._event_machines:
                        del self._event_machines[event_id]
                else:
                    return False, "Event already exists and is active"

            # Get or create user first (required for foreign key constraint)
            self.storage.get_or_create_user(creator_id, creator_name)
            
            # Create new event
            self.storage.create_event(event_id, group_name, creator_id)

            logger.info(f"Event {event_id} started by {creator_name}")
            return True, f"Event started: {group_name}"

        except Exception as e:
            error_msg = f"Failed to start event: {e}"
            self.error_handler(error_msg)
            return False, error_msg

    def close_event(self, event_id: int) -> tuple[bool, str]:
        """Close an event."""
        try:
            event = self.storage.get_event(event_id)
            if not event:
                return False, "Event not found"

            if event.state == EventState.CLOSED:
                return False, "Event is already closed"

            # Get event machine
            event_machine = self._get_event_machine(event_id)

            # Validate event state accepts CLOSE
            close_event = StateEvent('CLOSE', {})
            if not event_machine.current_state.validate(close_event):
                return False, f"Cannot close event in {event_machine.state_name} state"

            # Transition event state machine
            event_machine.transition(close_event)

            logger.info(f"Event {event_id} closed")
            return True, "Event closed successfully"

        except Exception as e:
            error_msg = f"Failed to close event: {e}"
            self.error_handler(error_msg)
            return False, error_msg

    def reset_event(self, event_id: int) -> tuple[bool, str]:
        """Reset an event (clear all participant data)."""
        try:
            event = self.storage.get_event(event_id)
            if not event:
                return False, "Event not found"

            # Reset all participants (clear debts/winnings, reset state)
            self.storage.reset_all_participants(event_id)

            # Reset event state to IDLE
            self.storage.update_event_state(event_id, EventState.IDLE)

            # Clear state machine cache
            if event_id in self._event_machines:
                del self._event_machines[event_id]

            logger.info(f"Event {event_id} reset")
            return True, "Event reset successfully"

        except Exception as e:
            error_msg = f"Failed to reset event: {e}"
            self.error_handler(error_msg)
            return False, error_msg

    def undo_last_bet(self, event_id: int) -> tuple[bool, str]:
        """Undo the last bet in an event."""
        try:
            event = self.storage.get_event(event_id)
            if not event:
                return False, "Event not found"

            if event.state == EventState.CLOSED:
                return False, "Cannot undo bets in a closed event"

            # Delete last participant
            success = self.storage.delete_last_participant(event_id)
            if not success:
                return False, "No bets to undo"

            # Check if event should transition back to IDLE
            in_game_count = self.storage.get_in_game_participant_count(event_id)
            if in_game_count == 0:
                # Update database state
                self.storage.update_event_state(event_id, EventState.IDLE)
                # Clear machine cache to force reload with new state
                if self._clear_event_machine:
                    self._clear_event_machine(event_id)
                elif event_id in self._event_machines:
                    del self._event_machines[event_id]

            logger.info(f"Event {event_id} undo last bet")
            return True, "Last bet undone successfully"

        except Exception as e:
            error_msg = f"Failed to undo last bet: {e}"
            self.error_handler(error_msg)
            return False, error_msg
