"""Telegram bot handlers for betting group commands."""

import logging
from decimal import Decimal
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from bot.group_manager import GroupManager
from settlement.calculator import SettlementCalculator
from settlement.ollama_agent import OllamaSettlementAgent

logger = logging.getLogger(__name__)

# Conversation states
BETTING, RESULTS, SETTLE = range(3)


class BettingHandler:
    """Handles Telegram commands for betting bot."""

    def __init__(self, group_manager: GroupManager, ollama_agent: Optional[OllamaSettlementAgent] = None):
        self.group_manager = group_manager
        self.ollama_agent = ollama_agent
        self.group_states = {}  # Track conversation state per group

    def _get_display_name(self, user) -> str:
        """Get display name from Telegram user object."""
        # Try username first (@username), then first_name + last_name, then fallback to User{id}
        if user.username:
            return user.username
        if user.first_name:
            name = user.first_name
            if user.last_name:
                name += f" {user.last_name}"
            return name
        return f"User{user.id}"

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle str command."""
        if not update.message or not update.message.chat:
            return ConversationHandler.END

        group_id = update.message.chat.id
        chat_title = update.message.chat.title or f"Group {group_id}"
        user_id = update.message.from_user.id

        # Create group if not exists
        if not self.group_manager.storage.get_group(group_id):
            self.group_manager.create_group(group_id, chat_title, user_id)

        await update.message.reply_text(
            "🎲 **Betting Bot Started!**\n\n"
            "Commands:\n"
            "• `b <amount>` - Place a bet (e.g., `b 50`)\n"
            "• `w <username> <prize>` - Record winnings (e.g., `w ron 100`)\n"
            "• `s` - Calculate settlements\n"
            "• `sts` - Show current group status\n"
            "• `t` - Show settlement transactions\n"
            "• `u` - Undo last bet\n"
            "• `r` - Reset all bets\n"
            "• `h` - Show help",
            parse_mode="Markdown",
        )
        return BETTING

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle h command - show all available commands."""
        help_text = """🎲 **Betting Bot Commands (Cash Game Model)**

**Group Management:**
• `str` - Initialize the bot for this group
• `h` - Show this help message

**Betting:**
• `b <amount>` - Place a bet (e.g., `b 50`)
• Or just send a number (e.g., `50`) to bet quickly
• `u` - Remove the last bet placed
• `r` - Reset all bets (empty the pot)

**Results:**
• `w <username> <prize>` - Record winnings when user leaves (e.g., `w ron 100`)

**Settlement:**
• `s` - Calculate optimal settlements (anytime)
• `sts` - Show current group status with in/out tracking
• `t` - Show settlement transactions

**Examples:**
```
b 100              # Place $100 bet
50                 # Quick bet of $50
w ron 150          # Ron wins $150 and leaves
s                  # Calculate settlements
sts                # Check status
u                  # Remove last bet
r                  # Reset all bets
```
"""
        await update.message.reply_text(help_text, parse_mode="Markdown")
        return BETTING

    async def new_chat_members(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle bot joining a new group - send welcome message."""
        if not update.message or not update.message.chat or not update.message.new_chat_members:
            return

        # Check if bot itself was added to the group
        bot_id = context.bot.id
        for member in update.message.new_chat_members:
            if member.id == bot_id:
                group_id = update.message.chat.id
                chat_title = update.message.chat.title or f"Group {group_id}"
                
                await update.message.reply_text(
                    "🎲 **Welcome to the Betting Bot!**\n\n"
                    "I'm here to help you manage group bets and calculate fair settlements.\n\n"
                    "To get started, type `str` to initialize this group.\n\n"
                    "Use `h` to see all available commands.",
                    parse_mode="Markdown",
                )
                break

    async def bet(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle b command."""
        if not update.message or not update.message.chat or not update.message.from_user:
            return BETTING

        group_id = update.message.chat.id
        user_id = update.message.from_user.id
        username = self._get_display_name(update.message.from_user)

        # Parse amount
        if not context.args or len(context.args) < 1:
            await update.message.reply_text("❌ Usage: `b <amount>` or just send a number", parse_mode="Markdown")
            return BETTING

        try:
            amount = Decimal(context.args[0])
            if amount <= 0:
                raise ValueError("Amount must be positive")
        except (ValueError, Exception):
            await update.message.reply_text("❌ Invalid amount. Use a positive number.", parse_mode="Markdown")
            return BETTING

        # Add bet
        success = self.group_manager.add_bet(group_id, user_id, username, amount)
        if success:
            await update.message.reply_text(
                f"✅ {username} placed a bet of ${amount:.2f}",
                parse_mode="Markdown",
            )
        else:
            await update.message.reply_text("❌ Failed to record bet.", parse_mode="Markdown")

        return BETTING

    async def handle_numeric_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle numeric messages as bets without /bet prefix."""
        if not update.message or not update.message.chat or not update.message.from_user:
            return BETTING

        group_id = update.message.chat.id
        user_id = update.message.from_user.id
        username = self._get_display_name(update.message.from_user)
        text = update.message.text.strip()

        # Check if message is a valid number
        try:
            amount = Decimal(text)
            if amount <= 0:
                return BETTING  # Ignore zero or negative numbers
        except (ValueError, Exception):
            return BETTING  # Not a number, ignore

        # Check if group exists
        if not self.group_manager.storage.get_group(group_id):
            await update.message.reply_text(
                "❌ Group not initialized. Please run `/start` first.",
                parse_mode="Markdown",
            )
            return BETTING

        # Add bet
        success = self.group_manager.add_bet(group_id, user_id, username, amount)
        if success:
            await update.message.reply_text(
                f"✅ {username} placed a bet of ${amount:.2f}",
                parse_mode="Markdown",
            )
        else:
            await update.message.reply_text("❌ Failed to record bet. Betting may be closed.", parse_mode="Markdown")

        return BETTING

    async def winner(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle w command - record winnings and mark user as out."""
        if not update.message or not update.message.chat:
            return BETTING

        group_id = update.message.chat.id

        # Parse winner and prize
        if not context.args or len(context.args) < 2:
            await update.message.reply_text("❌ Usage: `w <username> <prize_amount>`", parse_mode="Markdown")
            return BETTING

        try:
            prize = Decimal(context.args[1])
            if prize <= 0:
                raise ValueError("Prize must be positive")
        except (ValueError, Exception):
            await update.message.reply_text("❌ Invalid prize amount. Use a positive number.", parse_mode="Markdown")
            return BETTING

        # Try to parse as user_id first, then as username
        winner_identifier = context.args[0]
        winner_id = None

        try:
            # Try as numeric user_id
            winner_id = int(winner_identifier)
        except ValueError:
            # Not a number, treat as username - look up user_id
            participants = self.group_manager.storage.get_participants(group_id)
            for p in participants:
                if p.username.lower() == winner_identifier.lower():
                    winner_id = p.user_id
                    break

        if winner_id is None:
            await update.message.reply_text(f"❌ User '{winner_identifier}' not found in participants.", parse_mode="Markdown")
            return BETTING

        # Update winner
        winners = {winner_id: prize}
        success = self.group_manager.set_winners(group_id, winners)
        if success:
            await update.message.reply_text(f"🏆 {winner_identifier} recorded with winnings of ${prize:.2f} and marked as out.")
        else:
            await update.message.reply_text("❌ Failed to record winner.")

        return BETTING

    async def settle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle s command - calculate settlements."""
        if not update.message or not update.message.chat:
            return BETTING

        group_id = update.message.chat.id

        # Get participants
        summary = self.group_manager.get_group_summary(group_id)
        if not summary:
            await update.message.reply_text("❌ Group not found.", parse_mode="Markdown")
            return BETTING

        participants = summary["participants"]

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

        # Save and display
        if transactions:
            self.group_manager.save_settlement(group_id, transactions)

        # Format output
        output = self._format_settlement(transactions, participants)
        await update.message.reply_text(output, parse_mode="Markdown")

        return BETTING

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle sts command - show group status with in/out tracking."""
        if not update.message or not update.message.chat:
            return BETTING

        group_id = update.message.chat.id
        summary = self.group_manager.get_group_summary(group_id)

        if not summary:
            await update.message.reply_text("❌ Group not found.", parse_mode="Markdown")
            return BETTING

        output = self._format_status(summary)
        await update.message.reply_text(output, parse_mode="Markdown")
        return BETTING

    async def transactions(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle t command - show settlement transactions."""
        if not update.message or not update.message.chat:
            return BETTING

        group_id = update.message.chat.id
        transactions = self.group_manager.get_settlement_transactions(group_id)

        if not transactions:
            await update.message.reply_text("❌ No settlements found for this group.", parse_mode="Markdown")
            return BETTING

        output = "**Settlement Transactions:**\n\n"
        for tx in transactions:
            output += (
                f"{tx['from_username']} → {tx['to_username']}: "
                f"${tx['amount']:.2f}\n"
            )

        await update.message.reply_text(output, parse_mode="Markdown")
        return BETTING

    async def undo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle u command - remove last bet."""
        if not update.message or not update.message.chat:
            return BETTING

        group_id = update.message.chat.id

        # Check if group exists
        if not self.group_manager.storage.get_group(group_id):
            await update.message.reply_text("❌ Group not initialized. Please run `str` first.", parse_mode="Markdown")
            return BETTING

        # Undo last bet
        success = self.group_manager.undo_last_bet(group_id)
        if success:
            await update.message.reply_text("✅ Last bet removed.", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ No bets to undo.", parse_mode="Markdown")

        return BETTING

    async def reset(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle r command - reset all bets."""
        if not update.message or not update.message.chat:
            return BETTING

        group_id = update.message.chat.id

        # Check if group exists
        if not self.group_manager.storage.get_group(group_id):
            await update.message.reply_text("❌ Group not initialized. Please run `str` first.", parse_mode="Markdown")
            return BETTING

        # Reset all bets
        success = self.group_manager.reset_bets(group_id)
        if success:
            await update.message.reply_text("✅ All bets reset. Pot is empty.", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ Failed to reset bets.", parse_mode="Markdown")

        return BETTING

    def _format_settlement(self, transactions, participants) -> str:
        """Format settlement transactions for display."""
        if not transactions:
            return "✅ All participants break even! No settlements needed."

        output = "**Settlement Transactions:**\n\n"
        for from_uid, from_name, to_uid, to_name, amount in transactions:
            output += f"💸 {from_name} → {to_name}: **${amount:.2f}**\n"

        return output

    def _format_status(self, summary) -> str:
        """Format group status for display with in/out tracking."""
        output = f"**Group Status: {summary['status'].upper()}**\n\n"
        output += f"**Total Pot:** ${summary['total_pot']:.2f}\n"
        output += f"**Participants:** {len(summary['participants'])}\n\n"

        # Separate in and out participants
        in_players = [p for p in summary["participants"] if p.status == "in"]
        out_players = [p for p in summary["participants"] if p.status == "out"]

        if in_players:
            output += "**In Game:**\n"
            for p in in_players:
                output += f"- {p.username}: ${p.bet_amount:.2f}\n"

        if out_players:
            output += "\n**Out (Left):**\n"
            for p in out_players:
                output += f"- {p.username}: ${p.bet_amount:.2f} → ${p.prize_amount:.2f}\n"

        return output
