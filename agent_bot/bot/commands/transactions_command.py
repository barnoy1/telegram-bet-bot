"""Transactions command handler."""

from telegram import Update
from telegram.ext import ContextTypes
from agent_bot.bot.interfaces.command_handler import ICommandHandler

# Conversation state
BETTING = 0

# Track groups currently calculating settlement to block duplicate requests
_calculating_groups = set()


class TransactionsCommand(ICommandHandler):
    """Handler for the transactions command."""

    def __init__(self, event_service):
        self.event_service = event_service

    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle transactions command - show settlement transactions."""
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Transactions command called for group {update.message.chat.id if update.message else 'Unknown'}")
        
        if not update.message or not update.message.chat:
            return BETTING

        group_id = update.message.chat.id
        
        # Check if settlement is already being calculated for this group
        if group_id in _calculating_groups:
            await update.message.reply_text(
                "⏳ Settlement calculation in progress. Please wait...",
                parse_mode="Markdown"
            )
            return BETTING
        
        # Check if transactions already exist
        logger.info(f"Fetching transactions for event_id: {group_id}")
        transactions = self.event_service.get_transactions(group_id)
        logger.info(f"Transactions found: {len(transactions) if transactions else 0}")

        # If no transactions exist, trigger settlement calculation
        if not transactions:
            await self._calculate_and_show_settlement(update, group_id, logger)
            return BETTING

        # Show existing transactions
        output = (
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💸 *TRANSACTIONS* 💸\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        )
        for i, tx in enumerate(transactions, 1):
            # Need to get usernames from user service or participants
            output += f"{i}. User {tx['from_user_id']} → User {tx['to_user_id']}: ${tx['amount']:.2f}\n"
        
        output += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        await update.message.reply_text(output, parse_mode="Markdown")
        return BETTING

    async def _calculate_and_show_settlement(self, update: Update, group_id: int, logger):
        """Calculate settlement and show results."""
        # Mark group as calculating
        _calculating_groups.add(group_id)
        
        try:
            # Send calculating message
            calculating_msg = await update.message.reply_text(
                "⏳ Calculating settlement... This may take a moment.",
                parse_mode="Markdown"
            )
            
            # Calculate settlement via EventService
            success, message, transactions = self.event_service.calculate_settlement(group_id)
            
            if success and transactions:
                # Update message with results
                output = (
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "💸 *TRANSACTIONS* 💸\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                )
                for i, (from_uid, to_uid, amount) in enumerate(transactions, 1):
                    output += f"{i}. User {from_uid} → User {to_uid}: ${amount:.2f}\n"
                output += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                
                await calculating_msg.edit_text(output, parse_mode="Markdown")
            else:
                await calculating_msg.edit_text(
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "💸 *TRANSACTIONS* 💸\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    "📭 No settlement needed (everyone broke even).\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                    parse_mode="Markdown"
                )
        except Exception as e:
            logger.error(f"Error calculating settlement: {e}", exc_info=True)
            await update.message.reply_text(
                "❌ Error calculating settlement. Please try again.",
                parse_mode="Markdown"
            )
        finally:
            # Remove group from calculating set
            _calculating_groups.discard(group_id)
