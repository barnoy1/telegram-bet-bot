"""Bookie personality service for sassy bot responses."""

import random
from agent_bot.bot.personality.phrases import PhraseLibrary, PhraseCategory
from typing import Optional, Dict
from agent_bot.config.settings import PERSONALITY_ENABLED, PERSONALITY_SASSY_LEVEL


class Mood:
    """Mood states for the Sleazy persona volatility protocol."""
    FAKE_FRIENDLY = "fake_friendly"
    AGGRESSIVE_INSTIGATOR = "aggressive_instigator"
    SUPERSTITIOUS_HYPOCRITE = "superstitious_hypocrite"


class BookiePersonality:
    """Service for managing the sassy bookie personality (Sleazy)."""

    # Stage directions for atmospheric flourishes
    STAGE_DIRECTIONS = [
        "*Licks his thumb and starts counting a fresh stack of chips*",
        "*Adjusts a gold watch that clearly hasn't been set to the right time*",
        "*Taps his ring on the table as a player hesitates to bet*",
        "*Wipes a smudge off the table with a silk handkerchief and sighs*",
        "*Leans back and examines his fingernails*",
        "*Straightens his tie that costs more than your car*",
    ]

    def __init__(self, enabled: bool = None, sassy_level: str = None, language_service=None):
        """Initialize the bookie personality.
        
        Args:
            enabled: Whether the personality is enabled (uses config if not provided)
            sassy_level: The level of sassiness (low, medium, high) (uses config if not provided)
            language_service: Language service for translated phrases
        """
        self.enabled = enabled if enabled is not None else PERSONALITY_ENABLED
        self.sassy_level = sassy_level if sassy_level is not None else PERSONALITY_SASSY_LEVEL
        self.language_service = language_service

    def _get_mood(self) -> str:
        """Get current mood based on volatility protocol.
        
        Returns:
            Mood state: fake_friendly (40%), aggressive_instigator (40%), superstitious_hypocrite (20%)
        """
        roll = random.random()
        if roll < 0.4:
            return Mood.FAKE_FRIENDLY
        elif roll < 0.8:
            return Mood.AGGRESSIVE_INSTIGATOR
        else:
            return Mood.SUPERSTITIOUS_HYPOCRITE

    def _add_stage_direction(self, phrase: str) -> str:
        """Add a random stage direction to the phrase.
        
        Args:
            phrase: The base phrase
            
        Returns:
            Phrase with stage direction appended
        """
        if random.random() < 0.3:  # 30% chance to add stage direction
            direction = random.choice(self.STAGE_DIRECTIONS)
            return f"{phrase} {direction}"
        return phrase

    def get_rebuy_taunt(self, username: str) -> Optional[str]:
        """Get a sassy remark for a user who rebought.
        
        Args:
            username: The username of the rebuying user
            
        Returns:
            A sassy phrase or None if personality disabled
        """
        if not self.enabled:
            return None
        
        phrase = PhraseLibrary.get_phrase(PhraseCategory.REBUY)
        return self._add_stage_direction(phrase)

    def get_big_pot_out_taunt(self, username: str, pot_amount: float) -> Optional[str]:
        """Get a sassy remark for a user who out with a big pot.
        
        Args:
            username: The username of the user
            pot_amount: The amount of money in the pot
            
        Returns:
            A sassy phrase or None if personality disabled
        """
        if not self.enabled:
            return None
        
        # Only taunt if pot is significant (e.g., > $500)
        if pot_amount < 500:
            return None
        
        phrase = PhraseLibrary.get_phrase(
            PhraseCategory.BIG_POT_OUT,
            context={"pot": f"{pot_amount:.2f}"}
        )
        return self._add_stage_direction(phrase)

    def get_general_sassy(self, group_id: int = None) -> Optional[str]:
        """Get a general sassy remark.
        
        Args:
            group_id: Group ID for language detection
        
        Returns:
            A sassy phrase or None if personality disabled
        """
        if not self.enabled:
            return None
        
        # Try to get translated phrase if language service is available
        if self.language_service and group_id:
            try:
                # Get a random Hebrew phrase from the action section as general sassy
                # The he.yaml has action.standard_bet which can serve as general sassy
                phrase = self.language_service.get_translation(group_id, 'action.standard_bet')
                # Handle if translation returns a list
                if isinstance(phrase, list):
                    phrase = random.choice(phrase)
                return self._add_stage_direction(phrase)
            except Exception:
                # Fallback to English if translation fails
                pass
        
        phrase = PhraseLibrary.get_phrase(PhraseCategory.GENERAL_SASSY)
        return self._add_stage_direction(phrase)

    def get_inactivity_nasty(self) -> Optional[str]:
        """Get a nasty remark about group inactivity.
        
        Returns:
            A nasty phrase or None if personality disabled
        """
        if not self.enabled:
            return None
        
        phrase = PhraseLibrary.get_phrase(PhraseCategory.INACTIVITY_NASTY)
        return self._add_stage_direction(phrase)

    def get_greeting(self) -> Optional[str]:
        """Get a random greeting phrase.
        
        Returns:
            A greeting phrase or None if personality disabled
        """
        if not self.enabled:
            return None
        
        phrase = PhraseLibrary.get_phrase(PhraseCategory.GREETING)
        return self._add_stage_direction(phrase)

    def get_new_player_greeting(self, username: str) -> Optional[str]:
        """Get a greeting for a new player.
        
        Args:
            username: The username of the new player
            
        Returns:
            A greeting phrase or None if personality disabled
        """
        if not self.enabled:
            return None
        
        phrase = PhraseLibrary.get_phrase(PhraseCategory.NEW_PLAYER)
        return self._add_stage_direction(phrase)

    def get_bet_reaction(self, amount: float) -> Optional[str]:
        """Get a reaction to a bet being placed.
        
        Args:
            amount: The amount of the bet
            
        Returns:
            A reaction phrase or None if personality disabled
        """
        if not self.enabled:
            return None
        
        # Use big bet reaction for large amounts
        if amount >= 100:
            phrase = PhraseLibrary.get_phrase(PhraseCategory.BIG_BET)
        else:
            phrase = PhraseLibrary.get_phrase(PhraseCategory.BET_PLACED)
        
        return self._add_stage_direction(phrase)

    def get_hesitation_taunt(self) -> Optional[str]:
        """Get a taunt for a player hesitating.
        
        Returns:
            A taunt phrase or None if personality disabled
        """
        if not self.enabled:
            return None
        
        phrase = PhraseLibrary.get_phrase(PhraseCategory.HESITATION)
        return self._add_stage_direction(phrase)

    def get_winner_leaving_taunt(self, username: str) -> Optional[str]:
        """Get a taunt for a winner leaving the table.
        
        Args:
            username: The username of the leaving player
            
        Returns:
            A taunt phrase or None if personality disabled
        """
        if not self.enabled:
            return None
        
        phrase = PhraseLibrary.get_phrase(PhraseCategory.WINNER_LEAVING)
        return self._add_stage_direction(phrase)

    def get_loser_leaving_taunt(self, username: str) -> Optional[str]:
        """Get a taunt for a loser leaving the table.
        
        Args:
            username: The username of the leaving player
            
        Returns:
            A taunt phrase or None if personality disabled
        """
        if not self.enabled:
            return None
        
        phrase = PhraseLibrary.get_phrase(PhraseCategory.LOSER_LEAVING)
        return self._add_stage_direction(phrase)
