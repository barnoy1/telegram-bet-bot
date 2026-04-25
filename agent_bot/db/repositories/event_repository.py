"""Event repository for database operations."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import func, delete
from sqlalchemy.orm import Session

from agent_bot.db.models import Event, EventModel, EventState
from agent_bot.db.repositories.base_repository import BaseRepository


class EventRepository(BaseRepository):
    """Repository for event-related database operations."""

    def create_event(self, event_id: int, group_name: str, creator_id: int) -> Event:
        """Create a new event."""
        new_event = EventModel(
            event_id=event_id,
            group_name=group_name,
            creator_id=creator_id,
            state=EventState.IDLE
        )
        self.session.add(new_event)
        self.commit()
        self.session.refresh(new_event)
        return self._model_to_dataclass(new_event, Event)

    def get_event(self, event_id: int) -> Optional[Event]:
        """Get an event by ID."""
        event = self.session.query(EventModel).filter(
            EventModel.event_id == event_id
        ).first()
        return self._model_to_dataclass(event, Event)

    def update_event_state(self, event_id: int, state: EventState) -> bool:
        """Update event state."""
        event = self.session.query(EventModel).filter(
            EventModel.event_id == event_id
        ).first()
        if event:
            event.state = state
            self.commit()
            return True
        return False

    def close_event(self, event_id: int) -> bool:
        """Close an event."""
        event = self.session.query(EventModel).filter(
            EventModel.event_id == event_id
        ).first()
        if event:
            event.state = EventState.CLOSED
            event.closed_at = datetime.utcnow()
            self.commit()
            return True
        return False

    def update_event_activity(self, event_id: int) -> bool:
        """Update event activity timestamp."""
        event = self.session.query(EventModel).filter(
            EventModel.event_id == event_id
        ).first()
        if event:
            event.last_activity_timestamp = datetime.utcnow()
            self.commit()
            return True
        return False

    def delete_event(self, event_id: int) -> bool:
        """Delete an event (for cleanup)."""
        result = self.session.execute(
            delete(EventModel).where(EventModel.event_id == event_id)
        )
        self.commit()
        return result.rowcount > 0

    def get_all_events(self) -> List[Event]:
        """Get all events."""
        events = self.session.query(EventModel).all()
        return [self._model_to_dataclass(e, Event) for e in events]
