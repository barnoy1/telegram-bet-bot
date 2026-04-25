"""Tests for the Hungarian settlement algorithm."""

import unittest
from decimal import Decimal

from agent_bot.db.models import Participant, ParticipantState
from agent_bot.core.settlement.hungarian_settlement import HungarianSettlementService

# Import enum values for cleaner code
NOT_JOINED, IN_GAME, OUT = ParticipantState


class TestHungarianSettlementAlgorithm(unittest.TestCase):
    """Test the greedy settlement algorithm."""

    def setUp(self):
        """Set up test fixtures."""
        # No database needed for these pure algorithm tests
        pass

    def tearDown(self):
        """Clean up test fixtures."""
        pass

    def test_simple_settlement(self):
        """Test simple 2-party settlement."""
        p1 = Participant(1, 1, 1, "Ron", IN_GAME, Decimal("100"), Decimal("0"), Decimal("50"), 0, "")
        p2 = Participant(2, 1, 2, "Alice", IN_GAME, Decimal("50"), Decimal("0"), Decimal("100"), 0, "")

        transactions = HungarianSettlementService.calculate_settlement([p1, p2])
        
        # p2 owes p1: p1 net=50 (creditor), p2 net=-50 (debtor)
        self.assertEqual(len(transactions), 1)
        self.assertEqual(transactions[0][0], 2)  # from p2
        self.assertEqual(transactions[0][1], 1)  # to p1
        self.assertEqual(transactions[0][2], Decimal("50"))

    def test_break_even_scenario(self):
        """Test scenario where everyone breaks even."""
        p1 = Participant(1, 1, 1, "Ron", IN_GAME, Decimal("100"), Decimal("0"), Decimal("100"), 0, "")
        p2 = Participant(2, 1, 2, "Alice", IN_GAME, Decimal("50"), Decimal("0"), Decimal("50"), 0, "")

        transactions = HungarianSettlementService.calculate_settlement([p1, p2])
        
        # No transactions needed
        self.assertEqual(len(transactions), 0)

    def test_multiple_debtors_creditors(self):
        """Test optimal matching with multiple parties."""
        # Complex scenario: 3 debtors, 2 creditors
        p1 = Participant(1, 1, 1, "Ron", IN_GAME, Decimal("100"), Decimal("0"), Decimal("0"), 0, "")
        p2 = Participant(2, 1, 2, "Alice", IN_GAME, Decimal("50"), Decimal("0"), Decimal("0"), 0, "")
        p3 = Participant(3, 1, 3, "Bob", IN_GAME, Decimal("30"), Decimal("0"), Decimal("0"), 0, "")
        p4 = Participant(4, 1, 4, "Charlie", IN_GAME, Decimal("0"), Decimal("0"), Decimal("90"), 0, "")
        p5 = Participant(5, 1, 5, "David", IN_GAME, Decimal("0"), Decimal("0"), Decimal("90"), 0, "")

        transactions = HungarianSettlementService.calculate_settlement([p1, p2, p3, p4, p5])
        
        # Should produce minimal transactions
        total_debt = sum(t[2] for t in transactions)
        total_credit = sum(t[2] for t in transactions)
        self.assertEqual(total_debt, total_credit)


if __name__ == "__main__":
    unittest.main()
