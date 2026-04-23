"""Formatter for group status display."""

from typing import Dict, List
from agent_bot.db.storage import Participant
from agent_bot.bot.services.language_service import LanguageService


class StatusFormatter:
    """Status formatter for bot responses."""

    def __init__(self, language_service: LanguageService = None, group_id: int = None):
        self.language_service = language_service
        self.group_id = group_id

    def format(self, summary: dict) -> str:
        """Format group status summary."""
        participants = summary.get("participants", [])
        total_pot = summary.get("total_pot", 0)

        if self.language_service and self.group_id:
            header = self.language_service.get_translation(self.group_id, 'status.header')
            total_pot_label = self.language_service.get_translation(self.group_id, 'status.total_pot')
            players_label = self.language_service.get_translation(self.group_id, 'status.players')
            no_players = self.language_service.get_translation(self.group_id, 'status.no_players')
        else:
            # Fallback to English
            header = "POKER TABLE STATUS"
            total_pot_label = "Total Pot:"
            players_label = "Players:"
            no_players = "No players at the table yet."

        # Filter participants to only include IN_GAME and OUT (exclude NOT_JOINED)
        active_participants = [p for p in participants if p.state in ("IN_GAME", "OUT")]

        output = (
            f"🃏 **{header}** 🃏\n\n"
            f"💰 **{total_pot_label}** ${total_pot:.2f}\n\n"
        )

        if active_participants:
            output += f"👥 **{players_label}**:\n"
            for p in active_participants:
                status_emoji = "🎴" if p.state == "IN_GAME" else "🚪"
                output += f"{status_emoji} {p.username} - ${p.current_bet_amount:.2f} ({p.state})\n"
        else:
            output += f"📭 {no_players}\n"

        return output
