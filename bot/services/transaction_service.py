"""Transaction management service."""

import logging
from typing import List, Dict
from bot.services.group_service import GroupService

logger = logging.getLogger(__name__)


class TransactionService:
    """Service for managing settlement transactions."""

    def __init__(self, group_service: GroupService):
        self.group_service = group_service

    def save_settlement(self, group_id: int, transactions) -> bool:
        """Save settlement transactions.
        
        Args:
            group_id: Telegram group ID
            transactions: List of settlement transactions
            
        Returns:
            True if successful, False otherwise
        """
        return self.group_service.save_settlement(group_id, transactions)

    def get_transactions(self, group_id: int) -> List[Dict]:
        """Get settlement transactions for a group.
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            List of transaction dictionaries
        """
        return self.group_service.get_settlement_transactions(group_id)
