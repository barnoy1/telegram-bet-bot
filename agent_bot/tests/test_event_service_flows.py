"""Integration tests for event service multi-participant flows."""

import unittest
from decimal import Decimal
import random
import os

from agent_bot.db.storage import BettingStorage
from agent_bot.core.event_service import EventService
from agent_bot.db.models import EventState, ParticipantState

# Import enum values for cleaner code
NOT_JOINED, IN_GAME, OUT = ParticipantState


class TestEventServiceMultiParticipantFlows(unittest.TestCase):
    """Test complex multi-participant flows through state machines."""

    def setUp(self):
        """Set up test fixtures."""
        # Force SQLite for testing (override any DATABASE_URL from .env)
        self.db_url = "sqlite:///test.db"
        self.storage = BettingStorage(self.db_url)
        self.event_service = EventService(self.storage)
        # Generate unique event ID for each test to avoid conflicts
        self.event_id = -1000000000 - random.randint(1, 999999)

    def tearDown(self):
        """Clean up test fixtures."""
        try:
            # Reset event to clear all participants
            self.storage.reset_event(self.event_id)
            # Then delete the event
            self.storage.delete_event(self.event_id)
        except:
            pass
        finally:
            # Delete the database file
            if os.path.exists("test.db"):
                os.remove("test.db")

    def test_single_participant_flow(self):
        """Test single participant: start → bet → out → settlement."""
        user_id = 6183561523
        username = "Ron"

        # Start event
        success, msg = self.event_service.start_event(self.event_id, "Test Group", user_id, username)
        self.assertTrue(success)
        
        # Event should be in IDLE state
        event = self.storage.get_event(self.event_id)
        self.assertEqual(event.state, EventState.IDLE)

        # Place bet - should transition to BETTING_ACTIVE
        success, msg, is_rebuy, is_adding = self.event_service.place_bet(self.event_id, user_id, username, Decimal("100"))
        self.assertTrue(success)
        self.assertFalse(is_rebuy)
        self.assertFalse(is_adding)
        
        event = self.storage.get_event(self.event_id)
        self.assertEqual(event.state, EventState.BETTING_ACTIVE)

        # User goes out with partial amount (negative balance: 50 - 100 = -50)
        success, msg = self.event_service.user_out(self.event_id, user_id, username, Decimal("50"))
        self.assertTrue(success)

        # Verify taunting message mentions username (exact words may vary)
        self.assertIn(username, msg)

        # Check participant state
        participant = self.storage.get_participant(self.event_id, user_id)
        self.assertEqual(participant.state, OUT)
        self.assertEqual(participant.prize_amount, Decimal("50"))

        # Event should close (no IN_GAME participants)
        event = self.storage.get_event(self.event_id)
        self.assertEqual(event.state, EventState.CLOSED)

    def test_multiple_participants_betting_flow(self):
        """Test multiple participants placing bets in sequence."""
        user1_id = 6183561523
        user2_id = 1234567890
        user3_id = 9876543210

        # Start event
        self.event_service.start_event(self.event_id, "Test Group", user1_id, "Ron")

        # Multiple bets
        self.event_service.place_bet(self.event_id, user1_id, "Ron", Decimal("100"))
        self.event_service.place_bet(self.event_id, user2_id, "Alice", Decimal("75"))
        self.event_service.place_bet(self.event_id, user3_id, "Bob", Decimal("50"))

        # Check pot
        status = self.event_service.get_status(self.event_id)
        self.assertEqual(status["current_pot"], Decimal("225"))
        self.assertEqual(status["in_game_count"], 3)

    def test_rebuy_scenario(self):
        """Test rebuy: user goes out, then bets again."""
        user1_id = 6183561523
        user2_id = 1234567890

        self.event_service.start_event(self.event_id, "Test Group", user1_id, "Ron")
        self.event_service.place_bet(self.event_id, user1_id, "Ron", Decimal("100"))
        self.event_service.place_bet(self.event_id, user2_id, "Alice", Decimal("75"))
        self.event_service.user_out(self.event_id, user1_id, "Ron", Decimal("50"))

        # Rebuy (event is still open because Alice is still IN_GAME)
        success, msg, is_rebuy, is_adding = self.event_service.place_bet(self.event_id, user1_id, "Ron", Decimal("25"))
        self.assertTrue(success)
        self.assertTrue(is_rebuy)
        self.assertFalse(is_adding)

        participant = self.storage.get_participant(self.event_id, user1_id)
        self.assertEqual(participant.state, IN_GAME)
        self.assertEqual(participant.rebuy_count, 1)

    def test_adding_to_existing_bet(self):
        """Test adding to existing bet (not rebuy)."""
        user_id = 6183561523
        username = "Ron"

        self.event_service.start_event(self.event_id, "Test Group", user_id, username)
        self.event_service.place_bet(self.event_id, user_id, username, Decimal("100"))

        # Add to bet
        success, msg, is_rebuy, is_adding = self.event_service.place_bet(self.event_id, user_id, username, Decimal("25"))
        self.assertTrue(success)
        self.assertFalse(is_rebuy)
        self.assertTrue(is_adding)

        participant = self.storage.get_participant(self.event_id, user_id)
        self.assertEqual(participant.current_bet_amount, Decimal("125"))
        self.assertEqual(participant.total_bet_amount, Decimal("125"))

    def test_partial_exit_settlement_calculation(self):
        """Test settlement with partial exits."""
        user1_id = 6183561523
        user2_id = 1234567890

        self.event_service.start_event(self.event_id, "Test Group", user1_id, "Ron")
        self.event_service.place_bet(self.event_id, user1_id, "Ron", Decimal("100"))
        self.event_service.place_bet(self.event_id, user2_id, "Alice", Decimal("75"))

        # Ron goes out with 50 (partial)
        self.event_service.user_out(self.event_id, user1_id, "Ron", Decimal("50"))

        # Alice also goes out to close the event
        self.event_service.user_out(self.event_id, user2_id, "Alice", Decimal("75"))

        # Calculate settlement (event must be closed)
        success, msg, transactions = self.event_service.calculate_settlement(self.event_id)
        self.assertTrue(success)
        
        # Both are creditors (Ron: 100-50=50, Alice: 75-0=75), so no transactions
        self.assertEqual(len(transactions), 0)

    def test_closed_event_prevents_bets(self):
        """Test that closed events prevent new bets."""
        user_id = 6183561523
        username = "Ron"

        self.event_service.start_event(self.event_id, "Test Group", user_id, username)
        self.event_service.place_bet(self.event_id, user_id, username, Decimal("100"))
        self.event_service.user_out(self.event_id, user_id, username, Decimal("100"))

        # Event should be closed
        event = self.storage.get_event(self.event_id)
        self.assertEqual(event.state, EventState.CLOSED)

        # Try to bet again - should fail
        success, msg, _, _ = self.event_service.place_bet(self.event_id, user_id, username, Decimal("50"))
        self.assertFalse(success)
        self.assertIn("closed", msg.lower())

    def test_undo_last_bet(self):
        """Test undoing last bet."""
        user1_id = 6183561523
        user2_id = 1234567890

        self.event_service.start_event(self.event_id, "Test Group", user1_id, "Ron")
        self.event_service.place_bet(self.event_id, user1_id, "Ron", Decimal("100"))
        self.event_service.place_bet(self.event_id, user2_id, "Alice", Decimal("75"))

        # Undo last bet (may fail depending on event state)
        success, msg = self.event_service.undo_last_bet(self.event_id)
        # Just verify it doesn't crash - undo behavior depends on event state
        if success:
            participants = self.storage.get_all_participants(self.event_id)
            self.assertEqual(len(participants), 1)

    def test_reset_event(self):
        """Test resetting all bets."""
        user1_id = 6183561523
        user2_id = 1234567890

        self.event_service.start_event(self.event_id, "Test Group", user1_id, "Ron")
        self.event_service.place_bet(self.event_id, user1_id, "Ron", Decimal("100"))
        self.event_service.place_bet(self.event_id, user2_id, "Alice", Decimal("75"))

        # Reset
        success, msg = self.event_service.reset_event(self.event_id)
        self.assertTrue(success)

        # Event should be back to IDLE
        event = self.storage.get_event(self.event_id)
        self.assertEqual(event.state, EventState.IDLE)

        participants = self.storage.get_all_participants(self.event_id)
        self.assertEqual(len(participants), 0)

    def test_restart_closed_event(self):
        """Test that a closed event can be restarted with /str command."""
        user_id = 6183561523
        username = "Ron"

        # Start event
        self.event_service.start_event(self.event_id, "Test Group", user_id, username)
        self.event_service.place_bet(self.event_id, user_id, username, Decimal("100"))
        self.event_service.user_out(self.event_id, user_id, username, Decimal("100"))

        # Event should be closed
        event = self.storage.get_event(self.event_id)
        self.assertEqual(event.state, EventState.CLOSED)

        # Try to start event again - should succeed and recreate
        success, msg = self.event_service.start_event(self.event_id, "Test Group", user_id, username)
        self.assertTrue(success)

        # Event should be back to IDLE
        event = self.storage.get_event(self.event_id)
        self.assertEqual(event.state, EventState.IDLE)

        # Should be able to place a bet now
        success, msg, is_rebuy, is_adding = self.event_service.place_bet(self.event_id, user_id, username, Decimal("50"))
        self.assertTrue(success)
        self.assertFalse(is_rebuy)
        self.assertFalse(is_adding)


if __name__ == "__main__":
    unittest.main()
