"""Betting group management logic."""

import logging
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from db.storage import BettingStorage, Participant

logger = logging.getLogger(__name__)


class GroupManager:
    """Manages betting groups and their state."""

    def __init__(self, storage: BettingStorage):
        self.storage = storage
        self.active_groups: Dict[int, Dict] = {}  # group_id -> {status, phase}

    def create_group(self, group_id: int, group_name: str, creator_id: int) -> bool:
        """Create a new betting group."""
        try:
            self.storage.create_group(group_id, group_name, creator_id)
            self.active_groups[group_id] = {"phase": "betting", "closed": False}
            logger.info(f"Created group {group_id}: {group_name}")
            return True
        except Exception as e:
            logger.error(f"Error creating group: {e}")
            return False

    def add_bet(self, group_id: int, user_id: int, username: str, amount: Decimal) -> bool:
        """Add a bet from a user."""
        group = self.storage.get_group(group_id)
        if not group:
            logger.warning(f"Group {group_id} not found")
            return False

        if group_id in self.active_groups and self.active_groups[group_id].get("closed"):
            logger.warning(f"Group {group_id} is closed for betting")
            return False

        return self.storage.add_participant(group_id, user_id, username, amount)

    def close_betting(self, group_id: int) -> bool:
        """Close the betting phase."""
        if group_id not in self.active_groups:
            return False
        self.active_groups[group_id]["closed"] = True
        self.active_groups[group_id]["phase"] = "results"
        logger.info(f"Betting closed for group {group_id}")
        return True

    def set_winners(self, group_id: int, winners: Dict[int, Decimal]) -> bool:
        """Set winners and their prizes."""
        return self.storage.set_winners(group_id, winners)

    def get_group_summary(self, group_id: int) -> Optional[Dict]:
        """Get group summary: participants, bets, winners."""
        group = self.storage.get_group(group_id)
        if not group:
            return None

        participants = self.storage.get_participants(group_id)
        total_pot = sum(p.bet_amount for p in participants)
        winners = [p for p in participants if p.is_winner]

        return {
            "group": group,
            "participants": participants,
            "total_pot": total_pot,
            "winners": winners,
            "status": self.active_groups.get(group_id, {}).get("phase", "unknown"),
        }

    def validate_settlement(self, group_id: int) -> Tuple[bool, str]:
        """Validate that settlement can proceed."""
        summary = self.get_group_summary(group_id)
        if not summary:
            return False, "Group not found"

        if not summary["participants"]:
            return False, "No participants in group"

        if not summary["winners"]:
            return False, "No winners declared"

        total_pot = summary["total_pot"]
        total_prizes = sum(w.prize_amount for w in summary["winners"])

        if total_prizes > total_pot:
            return False, f"Prize total ({total_prizes}) exceeds pot ({total_pot})"

        return True, "Valid"

    def save_settlement(self, group_id: int, transactions: List[Tuple[int, str, int, str, Decimal]]) -> bool:
        """Save settlement transactions."""
        return self.storage.save_transactions(group_id, transactions)

    def get_settlement_transactions(self, group_id: int) -> List[Dict]:
        """Get settlement transactions for a group."""
        return self.storage.get_transactions(group_id)
