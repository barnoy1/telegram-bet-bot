"""Group management service."""

import logging
from typing import Dict, Optional
from bot.interfaces.group_service import IGroupService
from db.storage import BettingStorage

logger = logging.getLogger(__name__)


class GroupService(IGroupService):
    """Service for managing betting groups."""

    def __init__(self, storage: BettingStorage):
        self.storage = storage

    def create_group(self, group_id: int, group_name: str, creator_id: int) -> bool:
        """Create a new betting group."""
        try:
            self.storage.create_group(group_id, group_name, creator_id)
            logger.info(f"Created group {group_id}: {group_name}")
            return True
        except Exception as e:
            logger.error(f"Error creating group: {e}")
            return False

    def add_bet(self, group_id: int, user_id: int, username: str, amount) -> bool:
        """Add a bet from a user."""
        group = self.storage.get_group(group_id)
        if not group:
            logger.warning(f"Group {group_id} not found")
            return False

        return self.storage.add_participant(group_id, user_id, username, amount)

    def set_winners(self, group_id: int, winners: Dict[int, float]) -> bool:
        """Set winners and their prizes."""
        return self.storage.set_winners(group_id, winners)

    def get_group_summary(self, group_id: int) -> Optional[Dict]:
        """Get group summary: participants, bets, winners."""
        group = self.storage.get_group(group_id)
        if not group:
            return None

        participants = self.storage.get_participants(group_id)
        # Calculate total pot: for 'in' users add full bet, for 'out' users add (bet - prize)
        total_pot = sum(
            p.bet_amount - (p.prize_amount if p.status == 'out' else 0)
            for p in participants
        )
        winners = [p for p in participants if p.status == 'out']

        return {
            "group": group,
            "participants": participants,
            "total_pot": total_pot,
            "winners": winners,
            "status": "active",
        }

    def undo_last_bet(self, group_id: int) -> bool:
        """Remove the last bet placed in the group."""
        try:
            return self.storage.delete_last_participant(group_id)
        except Exception as e:
            logger.error(f"Error undoing last bet: {e}")
            return False

    def reset_bets(self, group_id: int) -> bool:
        """Reset all bets in the group."""
        try:
            return self.storage.delete_all_participants(group_id)
        except Exception as e:
            logger.error(f"Error resetting bets: {e}")
            return False

    def save_settlement(self, group_id: int, transactions) -> bool:
        """Save settlement transactions."""
        return self.storage.save_transactions(group_id, transactions)

    def get_settlement_transactions(self, group_id: int):
        """Get settlement transactions for a group."""
        return self.storage.get_transactions(group_id)
