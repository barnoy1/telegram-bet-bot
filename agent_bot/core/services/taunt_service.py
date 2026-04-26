"""Service for loading and generating taunts."""

import re
import random
from pathlib import Path
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class TauntService:
    """Service for loading and generating personality taunts."""

    def __init__(self):
        self._taunts = self._load_taunts_from_persona()

    def _load_taunts_from_persona(self) -> Dict[str, Dict[str, List[str]]]:
        """Load exit taunts from persona.md file organized by balance type and mood protocol."""
        taunts = {
            "positive": {"sadistic_mockery": [], "aggressive_instigator": []},
            "negative": {"sadistic_mockery": [], "aggressive_instigator": []},
            "break_even": {"sadistic_mockery": [], "aggressive_instigator": []}
        }

        try:
            persona_path = Path(__file__).parent.parent.parent / "persona" / "persona.md"
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

            logger.info("Successfully loaded taunts from persona.md")
            return taunts

        except Exception as e:
            logger.error(f"Failed to load persona file: {e}, using default taunts")
            return self._get_default_taunts()

    def _parse_mood_taunts(self, section_text: str, taunt_dict: Dict[str, List[str]]):
        """Parse taunts from a section, organizing by mood."""
        # Sadistic Mockery
        sadistic = re.search(r'Sadistic Mockery.*?\n(.*?)(?=Aggressive Instigator|\Z)', section_text, re.DOTALL)
        if sadistic:
            taunt_dict["sadistic_mockery"] = self._extract_taunts(sadistic.group(1))

        # Aggressive Instigator
        aggressive = re.search(r'Aggressive Instigator.*?\n(.*?)$', section_text, re.DOTALL)
        if aggressive:
            taunt_dict["aggressive_instigator"] = self._extract_taunts(aggressive.group(1))

    def _extract_taunts(self, text: str) -> List[str]:
        """Extract individual taunts from text."""
        taunts = []
        for line in text.split('\n'):
            line = line.strip()
            if line.startswith('-'):
                taunt = line[1:].strip()
                if taunt:
                    taunts.append(taunt)
        return taunts

    def _get_default_taunts(self) -> Dict[str, Dict[str, List[str]]]:
        """Get default taunts when persona file is not available."""
        return {
            "positive": {
                "sadistic_mockery": ["Look at {username} running away with ${balance:.2f} like a scared little bitch. Taking the money and crying all the way home. Your wife must be so proud of your cowardice. 💵"],
                "aggressive_instigator": ["What is this, {username}? Grabbing ${balance:.2f} and running like a little girl? Make a real move or get the hell out of my sight! 🃏"]
            },
            "negative": {
                "sadistic_mockery": ["Hey {username}! Down ${abs_balance:.2f}? Beautiful. I love watching you suffer. Your kids are gonna love the ramen dinners this month. Thanks for the donation, loser! 💸"],
                "aggressive_instigator": ["What is this, {username}? Down ${abs_balance:.2f} and running like a coward? This is a poker table or a daycare center? Pathetic! 😤"]
            },
            "break_even": {
                "sadistic_mockery": ["Hey {username}! Breaking even with ${prize_amount:.2f}? How boring. You're too scared to win and too scared to lose. Pathetic. 😊"],
                "aggressive_instigator": ["What is this, {username}? Breaking even with ${prize_amount:.2f}? This is a poker game or a knitting circle? Where's the balls? 🃏"]
            }
        }

    def generate_out_taunt(self, username: str, balance, prize_amount) -> str:
        """Generate a taunt for a player going out."""
        # Determine balance category
        if balance > 0:
            balance_category = "positive"
        elif balance < 0:
            balance_category = "negative"
        else:
            balance_category = "break_even"

        # Randomly select mood (50% each for sadistic_mockery and aggressive_instigator)
        mood = random.choice(["sadistic_mockery", "aggressive_instigator"])

        # Get taunts for this balance category and mood
        taunt_templates = self._taunts[balance_category][mood]

        # If no taunts loaded, fallback to default
        if not taunt_templates:
            logger.warning(f"No taunts found for {balance_category}/{mood}, using default")
            return self._get_default_taunts()[balance_category][mood][0].format(
                username=username,
                balance=balance if balance_category == "positive" else None,
                abs_balance=abs(balance) if balance_category == "negative" else None,
                prize_amount=prize_amount if balance_category == "break_even" else None
            )

        # Select random taunt and format it
        template = random.choice(taunt_templates)

        format_kwargs = {"username": username}
        if balance_category == "positive":
            format_kwargs["balance"] = balance
        elif balance_category == "negative":
            format_kwargs["abs_balance"] = abs(balance)
        else:  # break_even
            format_kwargs["prize_amount"] = prize_amount

        return template.format(**format_kwargs)
