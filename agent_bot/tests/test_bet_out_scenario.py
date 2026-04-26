"""Test for bet x then out y (x > y) scenario."""

import unittest
from decimal import Decimal
import random
import os

from agent_bot.db.storage import BettingStorage
from agent_bot.core.event_service import EventService
from agent_bot.db.models import EventState, ParticipantState
from agent_bot.tests.mock_llm_service import MockLLMPersonalityService

# Import enum values for cleaner code
NOT_JOINED, IN_GAME, OUT = ParticipantState


class TestBetOutScenario(unittest.TestCase):
    """Test scenario where user bets x then goes out with y (x > y)."""

    def setUp(self):
        """Set up test fixtures."""
        # Force SQLite for testing
        self.db_url = "sqlite:///test.db"
        self.storage = BettingStorage(self.db_url)
        self.mock_llm = MockLLMPersonalityService()
        self.event_service = EventService(self.storage, llm_service=self.mock_llm)
        # Generate unique event ID for each test to avoid conflicts
        self.event_id = -3000000000 - random.randint(1, 999999)

    def tearDown(self):
        """Clean up test fixtures."""
        try:
            self.storage.reset_event(self.event_id)
            self.storage.delete_event(self.event_id)
        except:
            pass
        finally:
            # Delete the database file
            if os.path.exists("test.db"):
                os.remove("test.db")

    def test_bet_x_out_y_greater_than_zero(self):
        """Test user bets 100, goes out with 60. Player should have 60 prize amount, pot should have 40 remaining."""
        user_id = 6183561523
        username = "Ron"
        bet_amount = Decimal("100")
        out_amount = Decimal("60")

        # Start event
        success, msg = self.event_service.start_event(self.event_id, "Test Group", user_id, username)
        self.assertTrue(success)

        # Place bet x
        result = self.event_service.place_bet(
            self.event_id, user_id, username, bet_amount
        )
        self.assertTrue(result.success)
        self.assertFalse(result.is_rebuy)
        self.assertFalse(result.is_adding)
        self.assertTrue(result.is_first_time)  # First bet should be marked as first time

        # Check pot after bet - should be x
        status = self.event_service.get_status(self.event_id)
        self.assertEqual(status["current_pot"], bet_amount)

        # User goes out with y (where y < x)
        success, msg = self.event_service.user_out(
            self.event_id, user_id, username, out_amount
        )
        self.assertTrue(success)

        # Verify taunting message mentions username (from TauntService)
        self.assertIn(username, msg)

        # Check participant state
        participant = self.storage.get_participant(self.event_id, user_id)
        self.assertEqual(participant.state, OUT)
        self.assertEqual(participant.prize_amount, out_amount)
        # Remaining bet amount should be bet - out_amount = 100 - 60 = 40
        self.assertEqual(participant.current_bet_amount, bet_amount - out_amount)

        # Check pot after user goes out - pot should be 40 (remaining from bet)
        status = self.event_service.get_status(self.event_id)
        self.assertEqual(status["current_pot"], bet_amount - out_amount)

        # Event should transition to IDLE (no IN_GAME participants)
        event = self.storage.get_event(self.event_id)
        self.assertEqual(event.state, EventState.IDLE)

    def test_bet_x_out_y_with_multiple_users(self):
        """Test multiple users with bet x then out y scenarios."""
        user1_id = 6183561523
        user2_id = 1234567890

        # Start event
        self.event_service.start_event(self.event_id, "Test Group", user1_id, "Ron")

        # Both users bet first
        self.event_service.place_bet(self.event_id, user1_id, "Ron", Decimal("100"))
        self.event_service.place_bet(self.event_id, user2_id, "Alice", Decimal("75"))

        # Then both go out
        success, msg1 = self.event_service.user_out(self.event_id, user1_id, "Ron", Decimal("60"))
        success, msg2 = self.event_service.user_out(self.event_id, user2_id, "Alice", Decimal("50"))

        # Verify taunting messages mention usernames
        self.assertIn("Ron", msg1)
        self.assertIn("Alice", msg2)

        # Check participants
        p1 = self.storage.get_participant(self.event_id, user1_id)
        p2 = self.storage.get_participant(self.event_id, user2_id)

        # Verify prize amounts
        self.assertEqual(p1.prize_amount, Decimal("60"))
        self.assertEqual(p2.prize_amount, Decimal("50"))

        # Verify bet amounts (reduced by prize amount when OUT)
        self.assertEqual(p1.current_bet_amount, Decimal("40"))  # 100 - 60
        self.assertEqual(p2.current_bet_amount, Decimal("25"))  # 75 - 50

        # Event should be IDLE (no IN_GAME participants)
        event = self.storage.get_event(self.event_id)
        self.assertEqual(event.state, EventState.IDLE)

    def test_bet_x_out_y_equal_amounts(self):
        """Test user bets x and goes out with same amount x (break even)."""
        user_id = 6183561523
        username = "Ron"
        bet_amount = Decimal("100")

        # Start event
        self.event_service.start_event(self.event_id, "Test Group", user_id, username)

        # Place bet x
        result = self.event_service.place_bet(self.event_id, user_id, username, bet_amount)
        self.assertTrue(result.success)

        # User goes out with same amount x
        success, msg = self.event_service.user_out(self.event_id, user_id, username, bet_amount)

        # Verify taunting message mentions username
        self.assertIn(username, msg)

        # Check participant
        participant = self.storage.get_participant(self.event_id, user_id)
        self.assertEqual(participant.prize_amount, bet_amount)
        # Remaining bet amount should be 0 (took everything)
        self.assertEqual(participant.current_bet_amount, Decimal("0"))

        # Check pot - should be 0 (no IN_GAME participants)
        status = self.event_service.get_status(self.event_id)
        self.assertEqual(status["current_pot"], Decimal("0"))


if __name__ == "__main__":
    unittest.main()
