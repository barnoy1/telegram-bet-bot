"""Formatter for group status display."""

from typing import Dict, List
from agent_bot.db.models import Participant


class StatusFormatter:
    """Status formatter for bot responses (English only)."""

    def __init__(self):
        pass

    def format(self, summary: dict) -> str:
        """Format group status summary."""
        participants = summary.get("participants", [])
        total_pot = summary.get("total_pot", 0)

        header = "POKER TABLE STATUS"
        total_pot_label = "Total Pot:"
        players_label = "Players:"
        no_players = "No players at the table yet."

        # Filter participants to only include IN_GAME and OUT (exclude NOT_JOINED)
        active_participants = [p for p in participants if p.state in ("IN_GAME", "OUT")]

        output = (
            f"🃏 {header} 🃏\n\n"
            f"💰 {total_pot_label}: ${total_pot:.2f}\n\n"
        )

        if active_participants:
            output += f"👥 {players_label}:\n"
            for p in active_participants:
                status_emoji = "🎴" if p.state == "IN_GAME" else "🚪"
                # For OUT state, show prize amount (what they took out)
                # For IN_GAME state, show prize amount if they have winnings, otherwise show current_bet
                if p.state.value == "OUT":
                    balance = p.prize_amount
                else:
                    # Show prize amount if > 0 (player has winnings), otherwise show current bet
                    balance = p.prize_amount if p.prize_amount > 0 else p.current_bet_amount
                output += f"{status_emoji} {p.username} - ${balance:.2f} ({p.state.value})\n"
        else:
            output += f"📭 {no_players}\n"

        return output
