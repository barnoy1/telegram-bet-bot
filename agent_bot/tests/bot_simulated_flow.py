"""Simulated betting flow test using mocked Telegram handler.

This test simulates a realistic betting competition by directly calling
bot handler methods instead of going through the Telegram API.
"""

import asyncio
import os
import sys
from unittest.mock import Mock, AsyncMock
from decimal import Decimal
from telegram import Update, User, Chat, Message
from telegram.ext import ContextTypes
from dotenv import load_dotenv

# Add parent directory to path to import bot modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from agent_bot.db.storage import BettingStorage
from agent_bot.core.event_service import EventService
from agent_bot.bot.telegram_handler import BettingHandler
from agent_bot.bot.services.language_service import LanguageService
from agent_bot.bot.personality.bookie_personality import BookiePersonality
from agent_bot.bot.personality.greetings import GreetingLibrary
from agent_bot.bot.services.inactivity_monitor import InactivityMonitor
from agent_bot.bot.commands.command_registry import CommandRegistry
from agent_bot.bot.commands.start_command import StartCommand
from agent_bot.bot.commands.help_command import HelpCommand
from agent_bot.bot.commands.out_command import OutCommand
from agent_bot.bot.commands.status_command import StatusCommand
from agent_bot.bot.commands.reset_command import ResetCommand

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '../../docker/.env'))

# Configuration from .env
TEST_CHAT_ID = int(os.getenv('TEST_CHAT_ID', '-1003833274922'))
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@db:5432/events')


class SimulatedUser:
    """Simulates a user for betting."""

    def __init__(self, user_id, username):
        self.user_id = user_id
        self.username = username

    def create_mock_update(self, text):
        """Create a mock Telegram Update object."""
        # Mock the entire message object to avoid Telegram library issues
        message = Mock()
        message.text = text
        message.message_id = 1
        message.chat_id = TEST_CHAT_ID
        message.chat = Mock()
        message.chat.id = TEST_CHAT_ID
        message.from_user = Mock()
        message.from_user.id = self.user_id
        message.from_user.username = self.username
        message.from_user.first_name = self.username
        message.reply_text = AsyncMock(return_value=Mock())
        
        update = Mock()
        update.message = message
        update.effective_chat = message.chat
        update.effective_chat.id = TEST_CHAT_ID
        update.effective_user = message.from_user
        return update


class BettingSimulation:
    """Simulates a realistic betting competition using mocked handlers."""

    def __init__(self):
        self.storage = BettingStorage(DATABASE_URL)
        self.event_service = EventService(self.storage)
        self.language_service = LanguageService(self.storage)
        self.personality = BookiePersonality(self.language_service)
        self.inactivity_monitor = InactivityMonitor(
            None,  # bot - not needed for testing
            self.personality, 
            self.storage,
            self.language_service
        )
        
        # Create command registry and register commands
        self.command_registry = CommandRegistry()
        self.command_registry.register("str", StartCommand(self.event_service, self.personality, self.language_service))
        self.command_registry.register("h", HelpCommand(self.event_service, self.personality, self.language_service))
        self.command_registry.register("out", OutCommand(self.event_service, self.personality))
        self.command_registry.register("s", StatusCommand(self.event_service, self.language_service))
        self.command_registry.register("r", ResetCommand(self.event_service))
        
        self.handler = BettingHandler(self.event_service, self.command_registry, self.personality, self.inactivity_monitor, self.language_service)
        self.users = []

    def initialize(self):
        """Initialize simulated users and services."""
        print("\n=== Initializing Simulation ===")
        
        user1 = SimulatedUser(8688725186, "UserBot1")
        user2 = SimulatedUser(8664577111, "UserBot2")
        
        self.users = [user1, user2]
        print(f"✓ Initialized {len(self.users)} simulated users")
        
        return True

    def create_mock_context(self, text):
        """Create a mock Telegram Context object."""
        context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        context.bot = AsyncMock()
        context.bot.send_message = AsyncMock(return_value=Mock())
        
        # Parse arguments from text
        if text.startswith('/'):
            context.args = []
        elif text.startswith('out '):
            # Extract the amount from "out 10"
            parts = text.split()
            context.args = parts[1:] if len(parts) > 1 else []
        else:
            context.args = []
        
        return context

    async def send_command(self, user_idx, text):
        """Send a command by calling the handler directly."""
        user = self.users[user_idx]
        update = user.create_mock_update(text)
        context = self.create_mock_context(text)
        
        print(f"  {user.username}: {text}")
        
        try:
            # Determine which handler to call based on the command
            if text.startswith('/'):
                if text == '/str':
                    await self.handler.start(update, context)
                elif text == '/s':
                    await self.handler.status(update, context)
                elif text == '/h':
                    await self.handler.help(update, context)
                elif text == '/r':
                    await self.handler.reset(update, context)
                else:
                    # Try as a command
                    await self.handler.handle_command(text[1:], update, context)
            elif text.startswith('out '):
                # Handle out command
                parts = text.split()
                if len(parts) == 2:
                    await self.handler.out(update, context)
            else:
                # Handle as numeric message (bet)
                await self.handler.handle_numeric_message(update, context)
            
            # Check if bot sent a response
            if context.bot.send_message.called:
                response = context.bot.send_message.call_args
                print(f"    → Bot response sent")
            
            await asyncio.sleep(0.5)  # Rate limiting
            return True
        except Exception as e:
            print(f"  ✗ Failed to process '{text}': {e}")
            import traceback
            traceback.print_exc()
            return False

    async def run_simulation(self):
        """Run the full betting simulation."""
        print("\n=== Starting Betting Simulation ===")
        print(f"Chat ID: {TEST_CHAT_ID}")
        print(f"Participants: {len(self.users)} users\n")

        # Phase 1: Start the game
        print("\n--- Phase 1: Starting the Game ---")
        await self.send_command(0, "/str")
        await asyncio.sleep(1)

        # Phase 2: Initial bets
        print("\n--- Phase 2: Initial Bets ---")
        bets = [
            (0, "50"),   # User1 bets 50
            (1, "75"),   # User2 bets 75
            (0, "25"),   # User1 adds 25 more
        ]
        
        for user_idx, amount in bets:
            await self.send_command(user_idx, amount)
            await asyncio.sleep(0.5)

        # Phase 3: Check status
        print("\n--- Phase 3: Check Status ---")
        await self.send_command(0, "/s")
        await asyncio.sleep(1)

        # Phase 4: Rebuy scenario
        print("\n--- Phase 4: Rebuy Scenario ---")
        # User1 goes out first
        await self.send_command(0, "out 10")
        await asyncio.sleep(1)
        
        # User1 rebuys
        await self.send_command(0, "100")  # Rebuy with 100
        await asyncio.sleep(1)

        # Phase 5: More betting
        print("\n--- Phase 5: Continued Betting ---")
        more_bets = [
            (1, "50"),   # User2 adds 50
            (0, "30"),   # User1 adds 30
            (1, "25"),   # User2 adds 25
        ]
        
        for user_idx, amount in more_bets:
            await self.send_command(user_idx, amount)
            await asyncio.sleep(0.5)

        # Phase 6: Check status again
        print("\n--- Phase 6: Check Status ---")
        await self.send_command(0, "/s")
        await asyncio.sleep(1)

        # Phase 7: Final outs
        print("\n--- Phase 7: Final Outs ---")
        await self.send_command(1, "out 20")  # User2 out with 20
        await asyncio.sleep(1)
        
        await self.send_command(0, "out 15")  # User1 out with 15
        await asyncio.sleep(1)

        # Phase 8: Final status
        print("\n--- Phase 8: Final Status ---")
        await self.send_command(0, "/s")
        await asyncio.sleep(1)

        # Phase 9: Reset for next round
        print("\n--- Phase 9: Reset for Next Round ---")
        await self.send_command(0, "/r")
        await asyncio.sleep(1)

        print("\n=== Simulation Complete ===")
        print("All bot methods called directly without Telegram API.")


async def main():
    """Main entry point for the simulation."""
    print("=" * 60)
    print("BETTING BOT SIMULATION TEST (Mocked Handler)")
    print("=" * 60)

    sim = BettingSimulation()
    
    if not sim.initialize():
        print("\n✗ Failed to initialize simulation.")
        return

    try:
        await sim.run_simulation()
    except KeyboardInterrupt:
        print("\n\nSimulation interrupted by user.")
    except Exception as e:
        print(f"\n✗ Simulation failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
