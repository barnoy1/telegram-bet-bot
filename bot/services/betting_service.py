"""Betting coordination service."""

import logging
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from bot.services.group_service import GroupService
from bot.services.participant_service import ParticipantService
from bot.services.settlement_service import SettlementService
from bot.services.transaction_service import TransactionService

logger = logging.getLogger(__name__)


class BettingService:
    """Service for coordinating betting operations."""

    def __init__(
        self,
        group_service: GroupService,
        participant_service: ParticipantService,
        settlement_service: SettlementService,
        transaction_service: TransactionService,
    ):
        self.group_service = group_service
        self.participant_service = participant_service
        self.settlement_service = settlement_service
        self.transaction_service = transaction_service

    def create_group(self, group_id: int, group_name: str, creator_id: int) -> bool:
        """Create a new betting group."""
        return self.group_service.create_group(group_id, group_name, creator_id)

    async def add_bet(self, group_id: int, user_id: int, username: str, amount: Decimal):
        """Add a bet for a participant.
        
        Returns:
            Tuple of (success: bool, is_rebuy: bool)
        """
        return await self.participant_service.add_bet(group_id, user_id, username, amount)

    def get_group_summary(self, group_id: int) -> Optional[Dict]:
        """Get group summary."""
        return self.group_service.get_group_summary(group_id)

    async def calculate_settlement(self, participants) -> List[Tuple]:
        """Calculate settlement transactions."""
        return await self.settlement_service.calculate_settlement(participants)

    def save_settlement(self, group_id: int, transactions) -> bool:
        """Save settlement transactions."""
        return self.transaction_service.save_settlement(group_id, transactions)

    def get_transactions(self, group_id: int) -> List[Dict]:
        """Get settlement transactions."""
        return self.transaction_service.get_transactions(group_id)

    def undo_last_bet(self, group_id: int) -> bool:
        """Remove the last bet."""
        return self.participant_service.undo_last_bet(group_id)

    def reset_bets(self, group_id: int) -> bool:
        """Reset all bets."""
        return self.participant_service.reset_all_bets(group_id)
