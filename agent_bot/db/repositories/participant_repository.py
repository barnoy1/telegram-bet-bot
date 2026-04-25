"""Participant repository for database operations."""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import func, delete
from sqlalchemy.orm import Session

from agent_bot.db.models import Participant, ParticipantModel, ParticipantState
from agent_bot.db.repositories.base_repository import BaseRepository

# Import enum values for cleaner code
NOT_JOINED, IN_GAME, OUT = ParticipantState


class ParticipantRepository(BaseRepository):
    """Repository for participant-related database operations."""

    def create_participant(self, event_id: int, user_id: int, bet_amount: Decimal) -> Participant:
        """Create a new participant with initial bet."""
        new_participant = ParticipantModel(
            event_id=event_id,
            user_id=user_id,
            state=IN_GAME,
            total_bet_amount=bet_amount,
            current_bet_amount=bet_amount
        )
        self.session.add(new_participant)
        self.commit()
        self.session.refresh(new_participant)
        return self._model_to_dataclass(new_participant, Participant)

    def get_participant(self, event_id: int, user_id: int) -> Optional[Participant]:
        """Get a participant by event and user ID."""
        participant = self.session.query(ParticipantModel).filter(
            ParticipantModel.event_id == event_id,
            ParticipantModel.user_id == user_id
        ).first()
        return self._model_to_dataclass(participant, Participant)

    def get_all_participants(self, event_id: int) -> List[Participant]:
        """Get all participants for an event."""
        participants = self.session.query(ParticipantModel).filter(
            ParticipantModel.event_id == event_id
        ).all()
        return [self._model_to_dataclass(p, Participant) for p in participants]

    def update_participant_bet(self, event_id: int, user_id: int, additional_amount: Decimal) -> bool:
        """Add to participant's current bet (and total)."""
        participant = self.session.query(ParticipantModel).filter(
            ParticipantModel.event_id == event_id,
            ParticipantModel.user_id == user_id
        ).first()
        if participant:
            participant.current_bet_amount += additional_amount
            participant.total_bet_amount += additional_amount
            participant.state = IN_GAME
            self.commit()
            return True
        return False

    def rebuy_participant(self, event_id: int, user_id: int, new_bet_amount: Decimal) -> bool:
        """Handle rebuy by resetting current_bet_amount to new amount and adding to total."""
        participant = self.session.query(ParticipantModel).filter(
            ParticipantModel.event_id == event_id,
            ParticipantModel.user_id == user_id
        ).first()
        if participant:
            participant.current_bet_amount = new_bet_amount
            participant.total_bet_amount += new_bet_amount
            participant.state = IN_GAME
            participant.settled_at = None
            self.commit()
            return True
        return False

    def set_participant_out(self, event_id: int, user_id: int, prize_amount: Decimal) -> bool:
        """Set participant as OUT with prize amount."""
        participant = self.session.query(ParticipantModel).filter(
            ParticipantModel.event_id == event_id,
            ParticipantModel.user_id == user_id
        ).first()
        if participant:
            participant.state = OUT
            participant.prize_amount = prize_amount
            participant.settled_at = datetime.utcnow()
            self.commit()
            return True
        return False

    def increment_rebuy_count(self, event_id: int, user_id: int) -> bool:
        """Increment participant's rebuy count."""
        participant = self.session.query(ParticipantModel).filter(
            ParticipantModel.event_id == event_id,
            ParticipantModel.user_id == user_id
        ).first()
        if participant:
            participant.rebuy_count = (participant.rebuy_count or 0) + 1
            self.commit()
            return True
        return False

    def delete_last_participant(self, event_id: int) -> bool:
        """Delete the most recent participant (for undo)."""
        participant = self.session.query(ParticipantModel).filter(
            ParticipantModel.event_id == event_id
        ).order_by(ParticipantModel.id.desc()).first()
        if participant:
            self.session.delete(participant)
            self.commit()
            return True
        return False

    def delete_all_participants(self, event_id: int) -> bool:
        """Delete all participants for an event (for reset)."""
        result = self.session.execute(
            delete(ParticipantModel).where(ParticipantModel.event_id == event_id)
        )
        self.commit()
        return result.rowcount > 0

    def get_in_game_participant_count(self, event_id: int) -> int:
        """Get count of IN_GAME participants."""
        count = self.session.query(ParticipantModel).filter(
            ParticipantModel.event_id == event_id,
            ParticipantModel.state == IN_GAME
        ).count()
        return count

    def get_current_pot(self, event_id: int) -> Decimal:
        """Calculate current pot (sum of current bets minus prizes for all participants)."""
        result = self.session.query(
            func.sum(ParticipantModel.current_bet_amount - ParticipantModel.prize_amount)
        ).filter(
            ParticipantModel.event_id == event_id
        ).scalar()
        if result:
            return Decimal(str(result))
        return Decimal("0")
