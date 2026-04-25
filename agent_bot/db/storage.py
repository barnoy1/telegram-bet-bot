"""PostgreSQL storage facade for betting bot using repository pattern."""

from decimal import Decimal
from typing import Optional, List, Dict
import logging

from sqlalchemy import create_engine, delete
from sqlalchemy.orm import sessionmaker, Session

from agent_bot.db.models import Base
from agent_bot.db.repositories import (
    EventRepository,
    ParticipantRepository,
    UserRepository,
    TransactionRepository,
    LanguageRepository
)
from agent_bot.config.settings import DATABASE_URL

logger = logging.getLogger(__name__)


class BettingStorage:
    """Facade for database operations using repository pattern."""

    def __init__(self, db_url: str = None):
        self.db_url = db_url or DATABASE_URL
        self.engine = create_engine(self.db_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        Base.metadata.create_all(self.engine)
        logger.info(f"Database initialized at {self.db_url}")

    def _get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()

    # User operations
    def get_or_create_user(self, user_id: int, username: str):
        """Get existing user or create new one."""
        with self._get_session() as session:
            repo = UserRepository(session)
            return repo.get_or_create_user(user_id, username)

    def get_user(self, user_id: int):
        """Get user by ID."""
        with self._get_session() as session:
            repo = UserRepository(session)
            return repo.get_user(user_id)

    # Event operations
    def create_event(self, event_id: int, group_name: str, creator_id: int):
        """Create a new event."""
        with self._get_session() as session:
            repo = EventRepository(session)
            return repo.create_event(event_id, group_name, creator_id)

    def get_event(self, event_id: int):
        """Get event by ID."""
        with self._get_session() as session:
            repo = EventRepository(session)
            return repo.get_event(event_id)

    def update_event_state(self, event_id: int, state) -> bool:
        """Update event state."""
        with self._get_session() as session:
            repo = EventRepository(session)
            return repo.update_event_state(event_id, state)

    def close_event(self, event_id: int) -> bool:
        """Close an event."""
        with self._get_session() as session:
            repo = EventRepository(session)
            return repo.close_event(event_id)

    def update_event_activity(self, event_id: int) -> bool:
        """Update event activity timestamp."""
        with self._get_session() as session:
            repo = EventRepository(session)
            return repo.update_event_activity(event_id)

    def delete_event(self, event_id: int) -> bool:
        """Delete an event (for cleanup)."""
        with self._get_session() as session:
            # Delete transactions first
            tx_repo = TransactionRepository(session)
            tx_repo.delete_transactions(event_id)
            # Delete participants
            part_repo = ParticipantRepository(session)
            part_repo.delete_all_participants(event_id)
            # Delete event
            event_repo = EventRepository(session)
            return event_repo.delete_event(event_id)

    def get_all_events(self) -> List:
        """Get all events."""
        with self._get_session() as session:
            repo = EventRepository(session)
            return repo.get_all_events()

    # Participant operations
    def get_participant(self, event_id: int, user_id: int):
        """Get participant by event and user ID."""
        with self._get_session() as session:
            repo = ParticipantRepository(session)
            return repo.get_participant(event_id, user_id)

    def get_all_participants(self, event_id: int) -> List:
        """Get all participants for an event."""
        with self._get_session() as session:
            repo = ParticipantRepository(session)
            return repo.get_all_participants(event_id)

    def create_participant(self, event_id: int, user_id: int, bet_amount: Decimal):
        """Create a new participant with initial bet."""
        with self._get_session() as session:
            repo = ParticipantRepository(session)
            return repo.create_participant(event_id, user_id, bet_amount)

    def update_participant_bet(self, event_id: int, user_id: int, additional_amount: Decimal) -> bool:
        """Add to participant's current bet (and total)."""
        with self._get_session() as session:
            repo = ParticipantRepository(session)
            return repo.update_participant_bet(event_id, user_id, additional_amount)

    def rebuy_participant(self, event_id: int, user_id: int, new_bet_amount: Decimal) -> bool:
        """Handle rebuy by resetting current_bet_amount to new amount and adding to total."""
        with self._get_session() as session:
            repo = ParticipantRepository(session)
            return repo.rebuy_participant(event_id, user_id, new_bet_amount)

    def set_participant_out(self, event_id: int, user_id: int, prize_amount: Decimal) -> bool:
        """Set participant as OUT with prize amount."""
        with self._get_session() as session:
            repo = ParticipantRepository(session)
            return repo.set_participant_out(event_id, user_id, prize_amount)

    def increment_rebuy_count(self, event_id: int, user_id: int) -> bool:
        """Increment participant's rebuy count."""
        with self._get_session() as session:
            repo = ParticipantRepository(session)
            return repo.increment_rebuy_count(event_id, user_id)

    def delete_last_participant(self, event_id: int) -> bool:
        """Delete the most recent participant (for undo)."""
        with self._get_session() as session:
            repo = ParticipantRepository(session)
            return repo.delete_last_participant(event_id)

    def delete_all_participants(self, event_id: int) -> bool:
        """Delete all participants for an event (for reset)."""
        with self._get_session() as session:
            repo = ParticipantRepository(session)
            return repo.delete_all_participants(event_id)

    # Transaction operations
    def save_transactions(self, event_id: int, transactions: List[Dict]) -> bool:
        """Save settlement transactions."""
        with self._get_session() as session:
            repo = TransactionRepository(session)
            for tx in transactions:
                repo.create_transaction(event_id, tx['from_user_id'], tx['to_user_id'], tx['amount'])
            return True

    def get_transactions(self, event_id: int) -> List:
        """Get all transactions for an event."""
        with self._get_session() as session:
            repo = TransactionRepository(session)
            return repo.get_transactions(event_id)

    # Utility operations
    def get_current_pot(self, event_id: int) -> Decimal:
        """Calculate current pot (sum of current bets minus prizes for all participants)."""
        with self._get_session() as session:
            repo = ParticipantRepository(session)
            return repo.get_current_pot(event_id)

    def get_in_game_participant_count(self, event_id: int) -> int:
        """Get count of IN_GAME participants."""
        with self._get_session() as session:
            repo = ParticipantRepository(session)
            return repo.get_in_game_participant_count(event_id)

    # Language tracking operations
    def increment_language(self, group_id: int, language_code: str) -> bool:
        """Increment language count for a group."""
        with self._get_session() as session:
            repo = LanguageRepository(session)
            return repo.increment_language(group_id, language_code)

    def get_language_stats(self, group_id: int) -> Dict[str, int]:
        """Get language statistics for a group."""
        with self._get_session() as session:
            repo = LanguageRepository(session)
            return repo.get_language_stats(group_id)

    def set_group_language(self, group_id: int, language_code: str) -> bool:
        """Set the group's language preference directly (clears existing stats)."""
        with self._get_session() as session:
            repo = LanguageRepository(session)
            return repo.set_group_language(group_id, language_code)
