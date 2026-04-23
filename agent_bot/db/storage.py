"""PostgreSQL storage for betting bot with state machine architecture using SQLAlchemy ORM."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict
import logging

from sqlalchemy import create_engine, func, select, delete
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError

from agent_bot.db.models import (
    User, Event, Participant, Transaction,
    EventState, ParticipantState,
    Base, UserModel, EventModel, ParticipantModel, TransactionModel, LanguageModel
)
from agent_bot.config.settings import DATABASE_URL

# Import enum values for cleaner code
NOT_JOINED, IN_GAME, OUT = ParticipantState

logger = logging.getLogger(__name__)


class BettingStorage:
    """Manages PostgreSQL database for betting bot with new schema using SQLAlchemy ORM."""

    def __init__(self, db_url: str = None):
        self.db_url = db_url or DATABASE_URL
        self.engine = create_engine(self.db_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        self._init_db()

    def _init_db(self):
        """Initialize database schema with new tables."""
        Base.metadata.create_all(self.engine)
        logger.info(f"Database initialized at {self.db_url}")

    def _get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()

    def _model_to_dataclass(self, model, dataclass_type):
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

    # User operations
    def get_or_create_user(self, user_id: int, username: str) -> User:
        """Get existing user or create new one."""
        with self._get_session() as session:
            # Try to get existing user
            user = session.query(UserModel).filter(UserModel.user_id == user_id).first()
            
            if user:
                # Update last_seen and username
                user.last_seen = datetime.utcnow()
                user.username = username
                session.commit()
                return self._model_to_dataclass(user, User)
            else:
                # Create new user
                new_user = UserModel(user_id=user_id, username=username)
                session.add(new_user)
                session.commit()
                session.refresh(new_user)
                return self._model_to_dataclass(new_user, User)

    def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        with self._get_session() as session:
            user = session.query(UserModel).filter(UserModel.user_id == user_id).first()
            return self._model_to_dataclass(user, User)

    # Event operations
    def create_event(self, event_id: int, group_name: str, creator_id: int) -> Event:
        """Create a new event."""
        with self._get_session() as session:
            new_event = EventModel(
                event_id=event_id,
                group_name=group_name,
                creator_id=creator_id,
                state=EventState.IDLE
            )
            session.add(new_event)
            session.commit()
            session.refresh(new_event)
            return self._model_to_dataclass(new_event, Event)

    def get_event(self, event_id: int) -> Optional[Event]:
        """Get event by ID."""
        with self._get_session() as session:
            event = session.query(EventModel).filter(EventModel.event_id == event_id).first()
            return self._model_to_dataclass(event, Event)

    def update_event_state(self, event_id: int, state: EventState) -> bool:
        """Update event state."""
        with self._get_session() as session:
            event = session.query(EventModel).filter(EventModel.event_id == event_id).first()
            if event:
                event.state = state
                session.commit()
                return True
            return False

    def close_event(self, event_id: int) -> bool:
        """Close an event."""
        with self._get_session() as session:
            event = session.query(EventModel).filter(EventModel.event_id == event_id).first()
            if event:
                event.state = EventState.CLOSED
                event.closed_at = datetime.utcnow()
                session.commit()
                return True
            return False

    def update_event_activity(self, event_id: int) -> bool:
        """Update event activity timestamp."""
        with self._get_session() as session:
            event = session.query(EventModel).filter(EventModel.event_id == event_id).first()
            if event:
                event.last_activity_timestamp = datetime.utcnow()
                session.commit()
                return True
            return False

    def delete_event(self, event_id: int) -> bool:
        """Delete an event (for cleanup)."""
        with self._get_session() as session:
            # Delete transactions first (foreign key dependency)
            session.execute(delete(TransactionModel).where(TransactionModel.event_id == event_id))
            # Delete participants
            session.execute(delete(ParticipantModel).where(ParticipantModel.event_id == event_id))
            # Delete event
            result = session.execute(delete(EventModel).where(EventModel.event_id == event_id))
            session.commit()
            return result.rowcount > 0

    def get_all_events(self) -> List[Event]:
        """Get all events."""
        with self._get_session() as session:
            events = session.query(EventModel).all()
            return [self._model_to_dataclass(event, Event) for event in events]

    # Participant operations
    def get_participant(self, event_id: int, user_id: int) -> Optional[Participant]:
        """Get participant by event and user ID."""
        with self._get_session() as session:
            participant = session.query(ParticipantModel).filter(
                ParticipantModel.event_id == event_id,
                ParticipantModel.user_id == user_id
            ).first()
            return self._model_to_dataclass(participant, Participant)

    def get_all_participants(self, event_id: int) -> List[Participant]:
        """Get all participants for an event."""
        with self._get_session() as session:
            participants = session.query(ParticipantModel).filter(
                ParticipantModel.event_id == event_id
            ).all()
            return [self._model_to_dataclass(p, Participant) for p in participants]

    def create_participant(self, event_id: int, user_id: int, bet_amount: Decimal) -> Participant:
        """Create a new participant with initial bet."""
        with self._get_session() as session:
            new_participant = ParticipantModel(
                event_id=event_id,
                user_id=user_id,
                state=IN_GAME,
                total_bet_amount=bet_amount,
                current_bet_amount=bet_amount
            )
            session.add(new_participant)
            session.commit()
            session.refresh(new_participant)
            return self._model_to_dataclass(new_participant, Participant)

    def update_participant_bet(self, event_id: int, user_id: int, additional_amount: Decimal) -> bool:
        """Add to participant's current bet (and total)."""
        with self._get_session() as session:
            participant = session.query(ParticipantModel).filter(
                ParticipantModel.event_id == event_id,
                ParticipantModel.user_id == user_id
            ).first()
            if participant:
                participant.current_bet_amount += additional_amount
                participant.total_bet_amount += additional_amount
                participant.state = IN_GAME
                session.commit()
                return True
            return False

    def rebuy_participant(self, event_id: int, user_id: int, new_bet_amount: Decimal) -> bool:
        """Handle rebuy by resetting current_bet_amount to new amount and adding to total."""
        with self._get_session() as session:
            participant = session.query(ParticipantModel).filter(
                ParticipantModel.event_id == event_id,
                ParticipantModel.user_id == user_id
            ).first()
            if participant:
                participant.current_bet_amount = new_bet_amount
                participant.total_bet_amount += new_bet_amount
                participant.state = IN_GAME
                participant.settled_at = None  # Clear settled timestamp
                session.commit()
                return True
            return False

    def set_participant_out(self, event_id: int, user_id: int, prize_amount: Decimal) -> bool:
        """Set participant as OUT with prize amount."""
        with self._get_session() as session:
            participant = session.query(ParticipantModel).filter(
                ParticipantModel.event_id == event_id,
                ParticipantModel.user_id == user_id
            ).first()
            if participant:
                participant.state = OUT
                participant.prize_amount = prize_amount
                participant.settled_at = datetime.utcnow()
                session.commit()
                return True
            return False

    def increment_rebuy_count(self, event_id: int, user_id: int) -> bool:
        """Increment participant's rebuy count."""
        with self._get_session() as session:
            participant = session.query(ParticipantModel).filter(
                ParticipantModel.event_id == event_id,
                ParticipantModel.user_id == user_id
            ).first()
            if participant:
                participant.rebuy_count = (participant.rebuy_count or 0) + 1
                session.commit()
                return True
            return False

    def delete_last_participant(self, event_id: int) -> bool:
        """Delete the most recent participant (for undo)."""
        with self._get_session() as session:
            participant = session.query(ParticipantModel).filter(
                ParticipantModel.event_id == event_id
            ).order_by(ParticipantModel.id.desc()).first()
            if participant:
                session.delete(participant)
                session.commit()
                return True
            return False

    def delete_all_participants(self, event_id: int) -> bool:
        """Delete all participants for an event (for reset)."""
        with self._get_session() as session:
            result = session.execute(delete(ParticipantModel).where(ParticipantModel.event_id == event_id))
            session.commit()
            return result.rowcount > 0

    # Transaction operations
    def save_transactions(self, event_id: int, transactions: List[Dict]) -> bool:
        """Save settlement transactions."""
        with self._get_session() as session:
            for tx in transactions:
                new_transaction = TransactionModel(
                    event_id=event_id,
                    from_user_id=tx['from_user_id'],
                    to_user_id=tx['to_user_id'],
                    amount=tx['amount']
                )
                session.add(new_transaction)
            session.commit()
            return True

    def get_transactions(self, event_id: int) -> List[Transaction]:
        """Get all transactions for an event."""
        with self._get_session() as session:
            transactions = session.query(TransactionModel).filter(
                TransactionModel.event_id == event_id
            ).all()
            return [self._model_to_dataclass(t, Transaction) for t in transactions]

    # Utility operations
    def get_current_pot(self, event_id: int) -> Decimal:
        """Calculate current pot (sum of current bets minus prizes for all participants)."""
        with self._get_session() as session:
            result = session.query(
                func.sum(ParticipantModel.current_bet_amount - ParticipantModel.prize_amount)
            ).filter(
                ParticipantModel.event_id == event_id
            ).scalar()
            if result:
                return Decimal(str(result))
            return Decimal("0")

    def get_in_game_participant_count(self, event_id: int) -> int:
        """Get count of IN_GAME participants."""
        with self._get_session() as session:
            count = session.query(ParticipantModel).filter(
                ParticipantModel.event_id == event_id,
                ParticipantModel.state == IN_GAME
            ).count()
            return count

    # Language tracking operations
    def increment_language(self, group_id: int, language_code: str) -> bool:
        """Increment language count for a group."""
        with self._get_session() as session:
            # Try to find existing record
            lang_record = session.query(LanguageModel).filter(
                LanguageModel.group_id == group_id,
                LanguageModel.language_code == language_code
            ).first()

            if lang_record:
                lang_record.count += 1
            else:
                lang_record = LanguageModel(
                    group_id=group_id,
                    language_code=language_code,
                    count=1
                )
                session.add(lang_record)

            session.commit()
            return True

    def get_language_stats(self, group_id: int) -> Dict[str, int]:
        """Get language statistics for a group."""
        with self._get_session() as session:
            results = session.query(LanguageModel).filter(
                LanguageModel.group_id == group_id
            ).all()
            return {r.language_code: r.count for r in results}
