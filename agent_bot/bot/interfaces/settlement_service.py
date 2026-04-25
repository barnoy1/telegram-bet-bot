"""Interface for settlement services."""

from abc import ABC, abstractmethod
from typing import List, Tuple
from decimal import Decimal
from agent_bot.db.models import Participant


class ISettlementService(ABC):
    """Interface for settlement calculation services."""

    @abstractmethod
    async def calculate_settlement(self, participants: List[Participant]) -> List[Tuple[int, str, int, str, Decimal]]:
        """Calculate settlement transactions for participants.
        
        Args:
            participants: List of participants with bets and winnings
            
        Returns:
            List of (from_user_id, from_username, to_user_id, to_username, amount) tuples
        """
        pass
