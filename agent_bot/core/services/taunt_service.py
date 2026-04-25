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
            "positive": {"fake_friendly": [], "aggressive": [], "superstitious": []},
            "negative": {"fake_friendly": [], "aggressive": [], "superstitious": []},
            "break_even": {"fake_friendly": [], "aggressive": [], "superstitious": []}
        }

        try:
            persona_path = Path(__file__).parent.parent.parent / "persona.md"
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
        # Fake Friendly
        fake_friendly = re.search(r'\*\*Fake Friendly.*?\*\*(.*?)(?=\*\*Aggressive|\*\*Superstitious|\Z)', section_text, re.DOTALL)
        if fake_friendly:
            taunt_dict["fake_friendly"] = self._extract_taunts(fake_friendly.group(1))

        # Aggressive
        aggressive = re.search(r'\*\*Aggressive.*?\*\*(.*?)(?=\*\*Superstitious|\Z)', section_text, re.DOTALL)
        if aggressive:
            taunt_dict["aggressive"] = self._extract_taunts(aggressive.group(1))

        # Superstitious
        superstitious = re.search(r'\*\*Superstitious.*?\*\*(.*?)$', section_text, re.DOTALL)
        if superstitious:
            taunt_dict["superstitious"] = self._extract_taunts(superstitious.group(1))

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
                "fake_friendly": ["Nice win, {username}!"],
                "aggressive": ["Took the money and ran, {username}?"],
                "superstitious": ["You broke the luck, {username}!"]
            },
            "negative": {
                "fake_friendly": ["Better luck next time, {username}!"],
                "aggressive": ["Tough break, {username}!"],
                "superstitious": ["Bad energy, {username}!"]
            },
            "break_even": {
                "fake_friendly": ["Safe and sound, {username}!"],
                "aggressive": ["Boring, {username}!"],
                "superstitious": ["Neutral energy, {username}!"]
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

        # Determine mood based on balance magnitude
        abs_balance = abs(balance)
        if abs_balance < 50:
            mood = "fake_friendly"  # 50%
        elif abs_balance < 150:
            mood = "aggressive"  # 30%
        else:
            mood = "superstitious"  # 20%

        # Get taunts for this balance category and mood
        taunt_templates = self._taunts[balance_category][mood]

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
