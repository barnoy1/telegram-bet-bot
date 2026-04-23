"""Event service to coordinate state machines and business logic."""

import logging
import random
import re
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Callable
from datetime import datetime
from pathlib import Path

from agent_bot.db.storage import BettingStorage
from agent_bot.db.models import Event, Participant, User, EventState, ParticipantState
from agent_bot.core.state_machine.event_state_machine import EventStateMachine
from agent_bot.core.state_machine.participant_state_machine import ParticipantStateMachine
from agent_bot.core.state_machine.base import Event as StateEvent
from agent_bot.core.settlement.hungarian_settlement import HungarianSettlementService

# Import enum values for cleaner code
NOT_JOINED, IN_GAME, OUT = ParticipantState

logger = logging.getLogger(__name__)


class EventService:
    """Service to manage event lifecycle and coordinate state machines."""

    def __init__(self, storage: BettingStorage, error_handler: Callable[[str], None] = None):
        self.storage = storage
        self.error_handler = error_handler or (lambda msg: logger.error(msg))
        # Cache for state machines (event_id -> machine)
        self._event_machines: Dict[int, EventStateMachine] = {}
        # Cache for participant state machines (event_id_user_id -> machine)
        self._participant_machines: Dict[str, ParticipantStateMachine] = {}
        # Load taunts from persona.md
        self._taunts = self._load_taunts_from_persona()

    def _get_event_machine(self, event_id: int) -> EventStateMachine:
        """Get or create event state machine."""
        if event_id not in self._event_machines:
            event = self.storage.get_event(event_id)
            if not event:
                raise ValueError(f"Event {event_id} not found")
            initial_state = EventState(event.state)
            self._event_machines[event_id] = EventStateMachine(
                self.storage, event_id, initial_state
            )
        return self._event_machines[event_id]

    def _get_participant_machine(self, event_id: int, user_id: int) -> ParticipantStateMachine:
        """Get or create participant state machine."""
        cache_key = f"{event_id}_{user_id}"
        if cache_key not in self._participant_machines:
            participant = self.storage.get_participant(event_id, user_id)
            if participant:
                initial_state = ParticipantState(participant.state)
            else:
                initial_state = NOT_JOINED
            self._participant_machines[cache_key] = ParticipantStateMachine(
                self.storage, event_id, user_id, initial_state
            )
        return self._participant_machines[cache_key]

    def _clear_participant_machine(self, event_id: int, user_id: int):
        """Clear participant state machine from cache."""
        cache_key = f"{event_id}_{user_id}"
        if cache_key in self._participant_machines:
            del self._participant_machines[cache_key]

    def _load_taunts_from_persona(self) -> Dict[str, Dict[str, List[str]]]:
        """Load exit taunts from persona.md file organized by balance type and mood protocol."""
        taunts = {
            "positive": {"fake_friendly": [], "aggressive": [], "superstitious": []},
            "negative": {"fake_friendly": [], "aggressive": [], "superstitious": []},
            "break_even": {"fake_friendly": [], "aggressive": [], "superstitious": []}
        }

        try:
            # Try to find persona.md in agent_bot directory
            persona_path = Path(__file__).parent.parent / "persona.md"
            if not persona_path.exists():
                logger.warning(f"Persona file not found at {persona_path}, using default taunts")
                return self._get_default_taunts()

            with open(persona_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse positive balance taunts by mood
            positive_section = re.search(r'\*\*Positive Balance.*?\*\*(.*?)(?=\*\*Negative|\*\*Break Even|\Z)', content, re.DOTALL)
            if positive_section:
                self._parse_mood_taunts(positive_section.group(1), taunts["positive"])

            # Parse negative balance taunts by mood
            negative_section = re.search(r'\*\*Negative Balance.*?\*\*(.*?)(?=\*\*Break Even|\*\*🎭|\Z)', content, re.DOTALL)
            if negative_section:
                self._parse_mood_taunts(negative_section.group(1), taunts["negative"])

            # Parse break even taunts by mood
            break_even_section = re.search(r'\*\*Break Even.*?\*\*(.*?)(?=\*\*🎭|\Z)', content, re.DOTALL)
            if break_even_section:
                self._parse_mood_taunts(break_even_section.group(1), taunts["break_even"])

            total = sum(len(mood) for mood_dict in taunts.values() for mood in mood_dict.values())
            logger.info(f"Loaded {total} taunts from persona.md organized by balance type and mood protocol")
            return taunts

        except Exception as e:
            logger.error(f"Failed to load taunts from persona.md: {e}, using defaults")
            return self._get_default_taunts()

    def _parse_mood_taunts(self, section: str, taunt_dict: Dict[str, List[str]]):
        """Parse a section of taunts organized by mood protocol."""
        # Parse Fake-Friendly taunts
        fake_friendly_match = re.search(r'Fake-Friendly \(40%\):(.*?)(?=Aggressive|Superstitious|\Z)', section, re.DOTALL)
        if fake_friendly_match:
            taunt_dict["fake_friendly"] = [
                line.strip().lstrip('-').strip().strip('"')
                for line in fake_friendly_match.group(1).split('\n')
                if line.strip().lstrip('-').strip()
            ]

        # Parse Aggressive Instigator taunts
        aggressive_match = re.search(r'Aggressive Instigator \(40%\):(.*?)(?=Superstitious|\Z)', section, re.DOTALL)
        if aggressive_match:
            taunt_dict["aggressive"] = [
                line.strip().lstrip('-').strip().strip('"')
                for line in aggressive_match.group(1).split('\n')
                if line.strip().lstrip('-').strip()
            ]

        # Parse Superstitious Hypocrite taunts
        superstitious_match = re.search(r'Superstitious Hypocrite \(20%\):(.*?)(?=\Z)', section, re.DOTALL)
        if superstitious_match:
            taunt_dict["superstitious"] = [
                line.strip().lstrip('-').strip().strip('"')
                for line in superstitious_match.group(1).split('\n')
                if line.strip().lstrip('-').strip()
            ]

    def _get_default_taunts(self) -> Dict[str, Dict[str, List[str]]]:
        """Return default hardcoded taunts as fallback organized by mood protocol."""
        return {
            "positive": {
                "fake_friendly": [
                    "Hey, hey! {username} walking away with ${balance:.2f} profit? Smart business, Champ! �",
                    "Breathe, {username}! You're up ${balance:.2f} and calling it a day? I respect the discipline! 🤝",
                ],
                "aggressive": [
                    "What is this, {username}? Grabbing ${balance:.2f} and running? Where's the guts? �",
                    "{username} snatches ${balance:.2f} from the soup and bolts! Make a REAL move! 🏃‍♂️",
                ],
                "superstitious": [
                    "{username} leaving with ${balance:.2f}? Don't mess up the vibes by leaving early! 🍀",
                    "You broke the flow, {username}! The universe remembers! ⚡",
                ]
            },
            "negative": {
                "fake_friendly": [
                    "Hey, {username}! Down ${abs_balance:.2f}? It's just paper, Killer! We're all friends here! �",
                    "Breathe, {username}! You're ${abs_balance:.2f} lighter but wiser, right? 🤗",
                ],
                "aggressive": [
                    "What is this, {username}? Down ${abs_balance:.2f} and running? Where's your pride? 😤",
                    "{username} bleeds ${abs_balance:.2f} and bolts? The collection plate was hungry! �",
                ],
                "superstitious": [
                    "{username} down ${abs_balance:.2f}? You were breathing on the cards! Bad energy! 😤",
                    "The chair was unlucky for you, {username}. You messed with the feng shui! 🪑",
                ]
            },
            "break_even": {
                "fake_friendly": [
                    "Hey, {username}! Breaking even with ${prize_amount:.2f}? That's what I call a peaceful night! �",
                    "Breathe, {username}! ${prize_amount:.2f} exactly? Safe and sound! 🤗",
                ],
                "aggressive": [
                    "What is this, {username}? Breaking even with ${prize_amount:.2f}? Where's the action? 😤",
                    "{username} plays it safe with ${prize_amount:.2f}? I'm falling asleep here! 😴",
                ],
                "superstitious": [
                    "{username} breaks even? You're neutralizing the cosmic balance! ⚖️",
                    "The table doesn't know whether to celebrate or cry, {username}! 🎭",
                ]
            }
        }

    def start_event(self, event_id: int, group_name: str, creator_id: int, creator_username: str) -> Tuple[bool, str]:
        """Start a new event (group)."""
        try:
            # Get or create user
            self.storage.get_or_create_user(creator_id, creator_username)
            
            # Check if event already exists
            existing_event = self.storage.get_event(event_id)
            if existing_event:
                if existing_event.state == EventState.CLOSED:
                    # Delete closed event and create new one
                    self.storage.delete_event(event_id)
                else:
                    return False, "Event already exists and is active"
            
            # Create new event
            event = self.storage.create_event(event_id, group_name, creator_id)
            
            # Create state machine
            self._event_machines[event_id] = EventStateMachine(
                self.storage, event_id, EventState.IDLE
            )
            
            logger.info(f"Started event {event_id}: {group_name}")
            return True, f"Event started: {group_name}"
        except Exception as e:
            error_msg = f"Failed to start event: {e}"
            self.error_handler(error_msg)
            return False, error_msg

    def place_bet(self, event_id: int, user_id: int, username: str, amount: Decimal) -> Tuple[bool, str, bool, bool]:
        """Place a bet for a participant."""
        try:
            # Validate amount
            if amount <= 0:
                return False, "Amount must be positive", False, False
            
            # Get or create user
            user = self.storage.get_or_create_user(user_id, username)
            
            # Get event
            event = self.storage.get_event(event_id)
            if not event:
                return False, "Event not found. Use /str to start.", False, False

            # Check if event is closed
            if event.state == EventState.CLOSED:
                return False, "Event is closed. Use /str to start a new event.", False, False
            
            # Get event machine
            event_machine = self._get_event_machine(event_id)
            
            # Validate event state accepts BET
            bet_event = StateEvent('BET', {'user_id': user_id, 'amount': amount})
            if not event_machine.current_state.validate(bet_event):
                return False, f"Cannot bet in {event_machine.state_name} state", False, False

            # Get participant machine
            participant_machine = self._get_participant_machine(event_id, user_id)

            # Validate participant state accepts BET
            if not participant_machine.current_state.validate(bet_event):
                return False, f"Cannot bet in participant {participant_machine.state_name} state", False, False
            
            # Get participant
            participant = self.storage.get_participant(event_id, user_id)
            previous_state = participant_machine.current_state
            
            # Handle bet placement
            if participant is None:
                # New participant
                self.storage.create_participant(event_id, user_id, amount)
                participant = self.storage.get_participant(event_id, user_id)
            else:
                # Existing participant
                if participant.state == OUT:
                    # Rebuy - reset current_bet_amount to new amount, add to total_bet_amount
                    self.storage.rebuy_participant(event_id, user_id, amount)
                    self.storage.increment_rebuy_count(event_id, user_id)
                else:
                    # Adding to existing bet
                    self.storage.update_participant_bet(event_id, user_id, amount)
            
            # Transition participant state machine
            participant_machine.transition(bet_event)
            
            # Check for rebuy or adding to bet
            is_rebuy = participant_machine.is_rebuy(previous_state)
            is_adding = participant_machine.is_adding_to_bet(previous_state)
            
            # Transition event state machine
            event_machine.transition(bet_event)
            
            # Update activity
            self.storage.update_event_activity(event_id)
            
            logger.info(f"Bet placed: {username} ${amount:.2f} in event {event_id}")
            return True, f"Bet placed: ${amount:.2f}", is_rebuy, is_adding
            
        except Exception as e:
            error_msg = f"Failed to place bet: {e}"
            self.error_handler(error_msg)
            return False, error_msg, False, False

    def _generate_out_taunt(self, username: str, balance: Decimal, prize_amount: Decimal) -> str:
        """Generate a taunting message based on user's balance when leaving, using Volatility Protocol."""
        # Determine balance category
        if balance > 0:
            balance_category = "positive"
            format_kwargs = {"username": username, "balance": balance}
        elif balance < 0:
            balance_category = "negative"
            format_kwargs = {"username": username, "balance": balance, "abs_balance": abs(balance)}
        else:
            balance_category = "break_even"
            format_kwargs = {"username": username, "prize_amount": prize_amount}

        # Select mood protocol based on Volatility Protocol percentages
        mood_roll = random.random()
        if mood_roll < 0.40:
            mood = "fake_friendly"  # 40%
        elif mood_roll < 0.80:
            mood = "aggressive"  # 40%
        else:
            mood = "superstitious"  # 20%

        # Get taunts for this balance category and mood
        taunt_templates = self._taunts[balance_category][mood]

        # Select random taunt and format it
        template = random.choice(taunt_templates)
        return template.format(**format_kwargs)

    def user_out(self, event_id: int, user_id: int, username: str, prize_amount: Decimal) -> Tuple[bool, str]:
        """Mark a user as OUT with prize amount."""
        try:
            # Validate amount
            if prize_amount <= 0:
                return False, "Amount must be positive"

            # Get event
            event = self.storage.get_event(event_id)
            if not event:
                return False, "Event not found"

            # Check if event is closed
            if event.state == EventState.CLOSED:
                return False, "Event is closed"

            # Get participant
            participant = self.storage.get_participant(event_id, user_id)
            if not participant:
                return False, "Participant not found in event"

            if participant.state != IN_GAME:
                return False, "Participant is not in game"

            # Validate against current pot
            current_pot = self.storage.get_current_pot(event_id)
            if prize_amount > current_pot:
                return False, f"Amount exceeds current pot (${current_pot:.2f})"

            # Get event machine
            event_machine = self._get_event_machine(event_id)

            # Validate event state accepts OUT
            out_event = StateEvent('OUT', {'user_id': user_id, 'amount': prize_amount})
            if not event_machine.current_state.validate(out_event):
                return False, f"Cannot go OUT in {event_machine.state_name} state"

            # Get participant machine
            participant_machine = self._get_participant_machine(event_id, user_id)

            # Validate participant state accepts OUT
            if not participant_machine.current_state.validate(out_event):
                return False, f"Cannot go OUT in participant {participant_machine.state_name} state"

            # Set participant as OUT
            self.storage.set_participant_out(event_id, user_id, prize_amount)

            # Calculate balance for taunt
            balance = prize_amount - participant.total_bet_amount

            # Generate taunting message
            taunt = self._generate_out_taunt(username, balance, prize_amount)

            # Transition participant state machine
            participant_machine.transition(out_event)

            # Transition event state machine
            event_machine.transition(out_event)

            # Check if event should close (no IN_GAME participants)
            close_event = StateEvent('CLOSE', {})
            event_machine.transition(close_event)

            # Update activity
            self.storage.update_event_activity(event_id)

            logger.info(f"User {username} went OUT with ${prize_amount:.2f} (balance: ${balance:.2f})")
            return True, taunt

        except Exception as e:
            error_msg = f"Failed to mark user OUT: {e}"
            self.error_handler(error_msg)
            return False, error_msg

    def get_status(self, event_id: int) -> Optional[Dict]:
        """Get event status summary."""
        try:
            event = self.storage.get_event(event_id)
            if not event:
                return None
            
            participants = self.storage.get_all_participants(event_id)
            current_pot = self.storage.get_current_pot(event_id)
            
            in_game = [p for p in participants if p.state == IN_GAME]
            out_players = [p for p in participants if p.state == OUT]
            
            return {
                "event": event,
                "state": event.state,
                "participants": participants,
                "in_game_count": len(in_game),
                "out_count": len(out_players),
                "current_pot": current_pot,
                "total_bets": sum(p.current_bet_amount for p in participants)
            }
        except Exception as e:
            self.error_handler(f"Failed to get status: {e}")
            return None

    def get_transactions(self, event_id: int) -> List[Dict]:
        """Get settlement transactions for an event."""
        try:
            transactions = self.storage.get_transactions(event_id)
            return [
                {
                    "from_user_id": tx.from_user_id,
                    "to_user_id": tx.to_user_id,
                    "amount": tx.amount,
                    "created_at": tx.created_at
                }
                for tx in transactions
            ]
        except Exception as e:
            self.error_handler(f"Failed to get transactions: {e}")
            return []

    def calculate_settlement(self, event_id: int) -> Tuple[bool, str, List[Tuple]]:
        """Calculate settlement transactions using greedy algorithm."""
        try:
            event = self.storage.get_event(event_id)
            if not event:
                return False, "Event not found", []
            
            participants = self.storage.get_all_participants(event_id)
            
            # Calculate transactions
            transactions = HungarianSettlementService.calculate_settlement(participants)
            
            # Save transactions
            tx_dicts = [
                {
                    "from_user_id": from_uid,
                    "to_user_id": to_uid,
                    "amount": amount
                }
                for from_uid, to_uid, amount in transactions
            ]
            self.storage.save_transactions(event_id, tx_dicts)
            
            logger.info(f"Calculated {len(transactions)} transactions for event {event_id}")
            return True, f"Settlement calculated: {len(transactions)} transactions", transactions
            
        except Exception as e:
            error_msg = f"Failed to calculate settlement: {e}"
            self.error_handler(error_msg)
            return False, error_msg, []

    def undo_last_bet(self, event_id: int) -> Tuple[bool, str]:
        """Undo the last bet placed in the event."""
        try:
            event = self.storage.get_event(event_id)
            if not event:
                return False, "Event not found"
            
            if event.state == EventState.CLOSED:
                return False, "Event is closed"
            
            # Delete last participant
            success = self.storage.delete_last_participant(event_id)
            if not success:
                return False, "No bets to undo"
            
            # Check if event should transition back to IDLE
            in_game_count = self.storage.get_in_game_participant_count(event_id)
            if in_game_count == 0:
                event_machine = self._get_event_machine(event_id)
                # Force transition to IDLE (this would need special handling)
                # For now, just update database
                self.storage.update_event_state(event_id, EventState.IDLE)
            
            logger.info(f"Undo last bet in event {event_id}")
            return True, "Last bet undone"
            
        except Exception as e:
            error_msg = f"Failed to undo bet: {e}"
            self.error_handler(error_msg)
            return False, error_msg

    def reset_event(self, event_id: int) -> Tuple[bool, str]:
        """Reset all bets in the event."""
        try:
            event = self.storage.get_event(event_id)
            if not event:
                return False, "Event not found"
            
            if event.state == EventState.CLOSED:
                return False, "Event is closed"
            
            # Delete all participants
            self.storage.delete_all_participants(event_id)
            
            # Reset event state to IDLE
            self.storage.update_event_state(event_id, EventState.IDLE)
            
            # Clear participant machine cache
            to_clear = [k for k in self._participant_machines.keys() if k.startswith(f"{event_id}_")]
            for key in to_clear:
                del self._participant_machines[key]
            
            # Recreate event machine in IDLE state
            self._event_machines[event_id] = EventStateMachine(
                self.storage, event_id, EventState.IDLE
            )
            
            logger.info(f"Reset event {event_id}")
            return True, "Event reset"
            
        except Exception as e:
            error_msg = f"Failed to reset event: {e}"
            self.error_handler(error_msg)
            return False, error_msg
