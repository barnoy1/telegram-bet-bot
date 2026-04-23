"""Interface for group services."""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, List, Optional, Tuple


class IGroupService(ABC):
    """Interface for group management services."""

    @abstractmethod
    def create_group(self, group_id: int, group_name: str, creator_id: int) -> bool:
        """Create a new betting group.
        
        Args:
            group_id: Telegram group ID
            group_name: Group name
            creator_id: User ID of the group creator
            
        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def add_bet(self, group_id: int, user_id: int, username: str, amount: Decimal) -> bool:
        """Add a bet from a user.
        
        Args:
            group_id: Telegram group ID
            user_id: Telegram user ID
            username: Display name of the user
            amount: Bet amount
            
        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def set_winners(self, group_id: int, winners: Dict[int, Decimal]) -> bool:
        """Set winners and their prizes.
        
        Args:
            group_id: Telegram group ID
            winners: Dictionary of user_id -> prize_amount
            
        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def get_group_summary(self, group_id: int) -> Optional[Dict]:
        """Get group summary including participants, bets, and winners.
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            Dictionary with group summary or None if not found
        """
        pass

    @abstractmethod
    def undo_last_bet(self, group_id: int) -> bool:
        """Remove the last bet placed in the group.
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def reset_bets(self, group_id: int) -> bool:
        """Reset all bets in the group.
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def save_settlement(self, group_id: int, transactions: List[Tuple[int, str, int, str, Decimal]]) -> bool:
        """Save settlement transactions.
        
        Args:
            group_id: Telegram group ID
            transactions: List of settlement transactions
            
        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def get_settlement_transactions(self, group_id: int) -> List[Dict]:
        """Get settlement transactions for a group.
        
        Args:
            group_id: Telegram group ID
            
        Returns:
            List of transaction dictionaries
        """
        pass
