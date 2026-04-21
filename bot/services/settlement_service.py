"""Settlement calculation service."""

import logging
from typing import List, Tuple, Optional
from decimal import Decimal
from bot.interfaces.settlement_service import ISettlementService
from settlement.calculator import SettlementCalculator
from settlement.ollama_agent import OllamaSettlementAgent
from db.storage import Participant

logger = logging.getLogger(__name__)


class SettlementService(ISettlementService):
    """Service for calculating settlement transactions."""

    def __init__(self, ollama_agent: Optional[OllamaSettlementAgent] = None):
        self.ollama_agent = ollama_agent

    async def calculate_settlement(self, participants: List[Participant]) -> List[Tuple[int, str, int, str, Decimal]]:
        """Calculate settlement transactions for participants.
        
        Args:
            participants: List of participants with bets and winnings
            
        Returns:
            List of (from_user_id, from_username, to_user_id, to_username, amount) tuples
        """
        # Try Ollama first, fallback to deterministic
        transactions = None
        if self.ollama_agent and self.ollama_agent._initialized:
            try:
                transactions = await self.ollama_agent.calculate_settlement(participants)
            except Exception as e:
                logger.warning(f"Ollama settlement failed: {e}")

        # Fallback to deterministic calculator
        if transactions is None:
            transactions = SettlementCalculator.calculate_settlement(participants)

        return transactions
