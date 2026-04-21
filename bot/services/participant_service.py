"""Participant management service."""

import logging
from decimal import Decimal
from bot.services.group_service import GroupService
from bot.services.settlement_service import SettlementService
from bot.personality.bookie_personality import BookiePersonality

logger = logging.getLogger(__name__)


class ParticipantService:
    """Service for managing participants and their bets."""

    def __init__(self, group_service: GroupService, settlement_service: SettlementService, personality: BookiePersonality = None):
        self.group_service = group_service
        self.settlement_service = settlement_service
        self.personality = personality or BookiePersonality()

    async def add_bet(self, group_id: int, user_id: int, username: str, amount: Decimal) -> bool:
        """Add a bet for a participant and trigger auto-settlement.
        
        Args:
            group_id: Telegram group ID
            user_id: Telegram user ID
            username: Display name of the user
            amount: Bet amount
            
        Returns:
            True if successful, False otherwise
        """
        # Check for rebuy (user was previously out)
        is_rebuy = self._check_rebuy(group_id, user_id)
        
        success = self.group_service.add_bet(group_id, user_id, username, amount)
        if success:
            # Return rebuy status for caller to handle taunt if needed
            if is_rebuy:
                return True, True  # success, is_rebuy
        return success, False

    def _check_rebuy(self, group_id: int, user_id: int) -> bool:
        """Check if user is rebuying (was previously out).
        
        Args:
            group_id: Telegram group ID
            user_id: Telegram user ID
            
        Returns:
            True if user was previously out, False otherwise
        """
        participants = self.group_service.storage.get_participants(group_id)
        for p in participants:
            if p.user_id == user_id and p.status == "out":
                return True
        return False

    def undo_last_bet(self, group_id: int) -> bool:
        """Remove the last bet placed in the group.
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            True if successful, False otherwise
        """
        return self.group_service.undo_last_bet(group_id)

    def reset_all_bets(self, group_id: int) -> bool:
        """Reset all bets in the group.
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            True if successful, False otherwise
        """
        return self.group_service.reset_bets(group_id)

    async def _trigger_auto_settlement(self, group_id: int) -> None:
        """Trigger automatic settlement calculation.
        
        Args:
            group_id: Telegram group ID
        """
        try:
            summary = self.group_service.get_group_summary(group_id)
            if summary and summary["participants"]:
                participants = summary["participants"]
                transactions = await self.settlement_service.calculate_settlement(participants)
                if transactions:
                    self.group_service.save_settlement(group_id, transactions)
        except Exception as e:
            logger.error(f"Error in auto-settlement: {e}")
