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
        """Handle rebuy by using prize money if available, then adding new money.

        Logic:
        - If new_bet_amount <= prize_amount: Use prize money, keep remainder
        - If new_bet_amount > prize_amount: Use all prize money, add difference as new money
        - current_bet_amount is added to (not overwritten) to preserve remaining pot from previous bet
        """
        participant = self.session.query(ParticipantModel).filter(
            ParticipantModel.event_id == event_id,
            ParticipantModel.user_id == user_id
        ).first()
        if participant:
            # Handle prize money usage
            if participant.prize_amount > 0:
                if new_bet_amount <= participant.prize_amount:
                    # Scenario 1: Rebuying with less than or equal to prize amount
                    # Use prize money, keep remainder
                    participant.prize_amount -= new_bet_amount
                else:
                    # Scenario 2: Rebuying with more than prize amount
                    # Use all prize money, the rest is new money
                    # prize_amount becomes 0, total_bet_amount increases by new_bet_amount
                    participant.prize_amount = Decimal("0")

            # Add new bet to current_bet_amount (preserves remaining pot from previous bet)
            participant.current_bet_amount += new_bet_amount
            participant.total_bet_amount += new_bet_amount
            participant.state = IN_GAME
            participant.settled_at = None
            self.commit()
            return True
        return False

    def set_participant_out(self, event_id: int, user_id: int, prize_amount: Decimal) -> bool:
        """Set participant as OUT with prize amount (accumulates with existing prize)."""
        participant = self.session.query(ParticipantModel).filter(
            ParticipantModel.event_id == event_id,
            ParticipantModel.user_id == user_id
        ).first()
        if participant:
            participant.state = OUT
            # Accumulate prize amount (add to existing prize if any)
            participant.prize_amount += prize_amount
            # Reduce current_bet_amount by prize_amount (what they're taking from pot)
            # If they bet 90 and take 60, remaining in pot is 30
            participant.current_bet_amount = max(Decimal("0"), participant.current_bet_amount - prize_amount)
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

    def reset_all_participants(self, event_id: int) -> bool:
        """Reset all participants for an event (clear debts/winnings, reset state)."""
        participants = self.session.query(ParticipantModel).filter(
            ParticipantModel.event_id == event_id
        ).all()
        for participant in participants:
            participant.state = NOT_JOINED
            participant.total_bet_amount = Decimal("0")
            participant.current_bet_amount = Decimal("0")
            participant.prize_amount = Decimal("0")
            participant.rebuy_count = 0
            participant.settled_at = None
        self.commit()
        return len(participants) > 0

    def get_in_game_participant_count(self, event_id: int) -> int:
        """Get count of IN_GAME participants."""
        count = self.session.query(ParticipantModel).filter(
            ParticipantModel.event_id == event_id,
            ParticipantModel.state == IN_GAME
        ).count()
        return count

    def get_current_pot(self, event_id: int) -> Decimal:
        """Calculate current pot (sum of current bets for IN_GAME players + remaining bets from OUT players)."""
        # Sum bets from IN_GAME players
        in_game_result = self.session.query(
            func.sum(ParticipantModel.current_bet_amount)
        ).filter(
            ParticipantModel.event_id == event_id,
            ParticipantModel.state == IN_GAME
        ).scalar()

        # Sum remaining bets from OUT players (what they left in the pot)
        out_result = self.session.query(
            func.sum(ParticipantModel.current_bet_amount)
        ).filter(
            ParticipantModel.event_id == event_id,
            ParticipantModel.state == OUT
        ).scalar()

        total = Decimal("0")
        if in_game_result:
            total += Decimal(str(in_game_result))
        if out_result:
            total += Decimal(str(out_result))

        return total
