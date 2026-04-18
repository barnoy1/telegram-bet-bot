"""Telegram bot handlers for betting group commands."""

import logging
from decimal import Decimal
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from bot.group_manager import GroupManager
from settlement.calculator import SettlementCalculator
from settlement.copilot_agent import CopilotSettlementAgent

logger = logging.getLogger(__name__)

# Conversation states
BETTING, RESULTS, SETTLE = range(3)


class BettingHandler:
    """Handles Telegram commands for betting bot."""

    def __init__(self, group_manager: GroupManager, copilot_agent: Optional[CopilotSettlementAgent] = None):
        self.group_manager = group_manager
        self.copilot_agent = copilot_agent
        self.group_states = {}  # Track conversation state per group

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle /start command."""
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
            "• `/bet <amount>` - Place a bet (e.g., `/bet 50`)\n"
            "• `/close` - Close betting phase\n"
            "• `/winner <user_id> <prize>` - Declare winner (e.g., `/winner 123 100`)\n"
            "• `/settle` - Calculate settlements\n"
            "• `/status` - Show current group status\n"
            "• `/transactions` - Show settlement transactions",
            parse_mode="Markdown",
        )
        return BETTING

    async def bet(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle /bet command."""
        if not update.message or not update.message.chat or not update.message.from_user:
            return BETTING

        group_id = update.message.chat.id
        user_id = update.message.from_user.id
        username = update.message.from_user.username or f"User{user_id}"

        # Parse amount
        if not context.args or len(context.args) < 1:
            await update.message.reply_text("❌ Usage: `/bet <amount>`", parse_mode="Markdown")
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
            await update.message.reply_text("❌ Failed to record bet. Betting may be closed.", parse_mode="Markdown")

        return BETTING

    async def close(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle /close command - close betting phase."""
        if not update.message or not update.message.chat:
            return BETTING

        group_id = update.message.chat.id
        self.group_manager.close_betting(group_id)
        await update.message.reply_text("🔒 Betting is now closed. Use `/winner` to declare winners.", parse_mode="Markdown")
        return RESULTS

    async def winner(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle /winner command - declare a winner."""
        if not update.message or not update.message.chat:
            return RESULTS

        group_id = update.message.chat.id

        # Parse winner_id and prize
        if not context.args or len(context.args) < 2:
            await update.message.reply_text("❌ Usage: `/winner <user_id> <prize_amount>`", parse_mode="Markdown")
            return RESULTS

        try:
            winner_id = int(context.args[0])
            prize = Decimal(context.args[1])
            if prize <= 0:
                raise ValueError("Prize must be positive")
        except (ValueError, Exception):
            await update.message.reply_text("❌ Invalid input. Use: `/winner <user_id> <prize>`", parse_mode="Markdown")
            return RESULTS

        # Update winner
        winners = {winner_id: prize}
        success = self.group_manager.set_winners(group_id, winners)
        if success:
            await update.message.reply_text(f"🏆 Winner declared: User {winner_id} wins ${prize:.2f}")
        else:
            await update.message.reply_text("❌ Failed to record winner.")

        return RESULTS

    async def settle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle /settle command - calculate settlements."""
        if not update.message or not update.message.chat:
            return SETTLE

        group_id = update.message.chat.id

        # Validate group can be settled
        valid, message = self.group_manager.validate_settlement(group_id)
        if not valid:
            await update.message.reply_text(f"❌ Cannot settle: {message}", parse_mode="Markdown")
            return SETTLE

        # Get participants
        summary = self.group_manager.get_group_summary(group_id)
        if not summary:
            await update.message.reply_text("❌ Group not found.", parse_mode="Markdown")
            return SETTLE

        participants = summary["participants"]

        # Try Copilot first, fallback to deterministic
        transactions = None
        if self.copilot_agent and self.copilot_agent._initialized:
            try:
                transactions = await self.copilot_agent.calculate_settlement(participants)
            except Exception as e:
                logger.warning(f"Copilot settlement failed: {e}")

        # Fallback to deterministic calculator
        if transactions is None:
            transactions = SettlementCalculator.calculate_settlement(participants)

        # Save and display
        if transactions:
            self.group_manager.save_settlement(group_id, transactions)

        # Format output
        output = self._format_settlement(transactions, participants)
        await update.message.reply_text(output, parse_mode="Markdown")

        return SETTLE

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle /status command - show group status."""
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
        """Handle /transactions command - show settlement transactions."""
        if not update.message or not update.message.chat:
            return SETTLE

        group_id = update.message.chat.id
        transactions = self.group_manager.get_settlement_transactions(group_id)

        if not transactions:
            await update.message.reply_text("❌ No settlements found for this group.", parse_mode="Markdown")
            return SETTLE

        output = "**Settlement Transactions:**\n\n"
        for tx in transactions:
            output += (
                f"{tx['from_username']} → {tx['to_username']}: "
                f"${tx['amount']:.2f}\n"
            )

        await update.message.reply_text(output, parse_mode="Markdown")
        return SETTLE

    def _format_settlement(self, transactions, participants) -> str:
        """Format settlement transactions for display."""
        if not transactions:
            return "✅ All participants break even! No settlements needed."

        output = "**Settlement Transactions:**\n\n"
        for from_uid, from_name, to_uid, to_name, amount in transactions:
            output += f"💸 {from_name} → {to_name}: **${amount:.2f}**\n"

        return output

    def _format_status(self, summary) -> str:
        """Format group status for display."""
        output = f"**Group Status: {summary['status'].upper()}**\n\n"
        output += f"**Total Pot:** ${summary['total_pot']:.2f}\n"
        output += f"**Participants:** {len(summary['participants'])}\n\n"

        output += "**Bets:**\n"
        for p in summary["participants"]:
            output += f"- {p.username}: ${p.bet_amount:.2f}\n"

        if summary["winners"]:
            output += "\n**Winners:**\n"
            for w in summary["winners"]:
                output += f"- {w.username}: ${w.prize_amount:.2f}\n"

        return output
