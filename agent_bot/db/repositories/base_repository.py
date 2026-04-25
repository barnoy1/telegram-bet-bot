"""Base repository with common database operations."""

from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from typing import TypeVar, Type, Optional
import logging

from agent_bot.db.models import (
    User, Event, Participant, Transaction,
    UserModel, EventModel, ParticipantModel, TransactionModel
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BaseRepository:
    """Base repository with common database operations."""

    def __init__(self, session: Session):
        self.session = session

    def _model_to_dataclass(self, model, dataclass_type: Type[T]) -> Optional[T]:
        """Convert SQLAlchemy model to dataclass."""
        if model is None:
            return None

        if isinstance(model, UserModel):
            return User(
                user_id=model.user_id,
                username=model.username,
                first_seen=model.first_seen.isoformat() if model.first_seen else "",
                last_seen=model.last_seen.isoformat() if model.last_seen else ""
            )
        elif isinstance(model, EventModel):
            return Event(
                event_id=model.event_id,
                group_name=model.group_name,
                creator_id=model.creator_id,
                state=model.state,
                created_at=model.created_at.isoformat() if model.created_at else "",
                closed_at=model.closed_at.isoformat() if model.closed_at else None,
                last_activity_timestamp=model.last_activity_timestamp.isoformat() if model.last_activity_timestamp else None
            )
        elif isinstance(model, ParticipantModel):
            username = model.user.username if model.user else f"User_{model.user_id}"
            return Participant(
                id=model.id,
                event_id=model.event_id,
                user_id=model.user_id,
                username=username,
                state=model.state,
                total_bet_amount=Decimal(str(model.total_bet_amount)) if model.total_bet_amount else Decimal("0"),
                current_bet_amount=Decimal(str(model.current_bet_amount)) if model.current_bet_amount else Decimal("0"),
                prize_amount=Decimal(str(model.prize_amount)) if model.prize_amount else Decimal("0"),
                rebuy_count=model.rebuy_count or 0,
                joined_at=model.joined_at.isoformat() if model.joined_at else "",
                settled_at=model.settled_at.isoformat() if model.settled_at else None
            )
        elif isinstance(model, TransactionModel):
            return Transaction(
                id=model.id,
                event_id=model.event_id,
                from_user_id=model.from_user_id,
                to_user_id=model.to_user_id,
                amount=Decimal(str(model.amount)) if model.amount else Decimal("0"),
                created_at=model.created_at.isoformat() if model.created_at else ""
            )
        return None

    def commit(self):
        """Commit the current session."""
        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to commit: {e}")
            raise

    def rollback(self):
        """Rollback the current session."""
        self.session.rollback()
