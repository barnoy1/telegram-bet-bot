"""Formatter for settlement transactions display."""

from typing import List, Tuple
from decimal import Decimal


class SettlementFormatter:
    """Formats settlement transactions for display."""

    @staticmethod
    def format(transactions: List[Tuple[int, str, int, str, Decimal]]) -> str:
        """Format settlement transactions."""
        if not transactions:
            return (
                "━━━━━━━━━━━━━\n"
                "💸 *SETTLEMENTS* 💸\n"
                "━━━━━━━━━━━━━\n\n"
                "✅ All participants break even! No settlements needed.\n"
                "━━━━━━━━━━━━━"
            )
        
        output = (
            "━━━━━━━━━━━━━\n"
            "💸 *SETTLEMENTS* 💸\n"
            "━━━━━━━━━━━━━\n\n"
        )
        for i, tx in enumerate(transactions, 1):
            output += f"{i}. {tx[1]} → {tx[3]}: ${tx[4]:.2f}\n"
        
        output += "\n━━━━━━━━━━━━━"
        return output
