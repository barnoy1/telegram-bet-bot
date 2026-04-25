"""LLM-based persona service for generating dynamic responses."""

import logging
import httpx
from typing import Optional, Dict
from agent_bot.config.settings import OLLAMA_BASE_URL, OLLAMA_MODEL

logger = logging.getLogger(__name__)


class LLMPersonalityService:
    """Service for generating persona responses using LLM."""

    def __init__(self, base_url: str = None, model: str = None):
        """Initialize LLM personality service.
        
        Args:
            base_url: Ollama base URL (from config if not provided)
            model: LLM model name (from config if not provided)
        """
        self.base_url = base_url or OLLAMA_BASE_URL
        self.model = model or OLLAMA_MODEL
        self.timeout = 30  # seconds

    def _load_persona_prompt(self) -> str:
        """Load the persona definition from persona.md."""
        try:
            from pathlib import Path
            # Try multiple possible paths for persona.md
            possible_paths = [
                Path(__file__).parent.parent.parent / 'persona' / 'persona.md',
                Path(__file__).parent.parent / 'persona.md',
                Path('/app/agent_bot/persona/persona.md'),
                Path('/app/persona.md')
            ]
            
            for persona_path in possible_paths:
                if persona_path.exists():
                    with open(persona_path, 'r', encoding='utf-8') as f:
                        logger.info(f"Loaded persona from {persona_path}")
                        return f.read()
            
            logger.warning("Persona.md not found in any expected location")
            return ""
        except Exception as e:
            logger.error(f"Failed to load persona.md: {e}")
            return ""

    def _generate_response(self, prompt: str) -> Optional[str]:
        """Generate response using Ollama LLM.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            Generated response or None if failed
        """
        try:
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.8,
                    "top_p": 0.9,
                    "max_tokens": 150
                }
            }
            
            response = httpx.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "").strip()
        except Exception as e:
            logger.error(f"Failed to generate LLM response: {e}")
            return None

    def get_rebuy_response(self, username: str) -> Optional[str]:
        """Generate a response for a user rebuy.
        
        Args:
            username: The username of the rebuying user
            
        Returns:
            Generated response or None if failed
        """
        persona = self._load_persona_prompt()
        prompt = f"""You are a poker room dealer named Sleazy. You are cynical, street-smart, and obnoxiously performative. You view every player as a "mark" or an "asset."

Situation: {username} is rebuying - they previously left the table and now they're back with more money to bet again.

Your task: Generate a sassy, cynical comment about this rebuy. Be sarcastic but not mean. Use poker metaphors and street slang. Keep it brief (1-2 sentences).

{persona}

Response:"""
        
        return self._generate_response(prompt)

    def get_bet_response(self, username: str, amount: float) -> Optional[str]:
        """Generate a response for a bet being placed.
        
        Args:
            username: The username of the player
            amount: The amount of the bet
            
        Returns:
            Generated response or None if failed
        """
        persona = self._load_persona_prompt()
        is_big_bet = amount >= 100
        
        bet_type = "big/hero move" if is_big_bet else "standard"
        prompt = f"""You are a poker room dealer named Sleazy. You are cynical, street-smart, and obnoxiously performative. You view every player as a "mark" or an "asset."

Situation: {username} just placed a bet of ${amount:.2f}. This is a {bet_type} bet.

Your task: Generate a sassy, cynical comment about this bet. Use poker metaphors and street slang. Keep it brief (1-2 sentences).

{persona}

Response:"""
        
        return self._generate_response(prompt)

    def get_out_response(self, username: str, balance: float) -> Optional[str]:
        """Generate a response for a user leaving the table.
        
        Args:
            username: The username of the leaving player
            balance: The player's balance (positive = profit, negative = loss)
            
        Returns:
            Generated response or None if failed
        """
        persona = self._load_persona_prompt()
        
        if balance > 0:
            situation = f"{username} is leaving with ${balance:.2f} profit (winner)"
            mood_hint = "Use the 'cowardice' angle - they're taking money and running"
        elif balance < 0:
            situation = f"{username} is leaving down ${abs(balance):.2f} (loser)"
            mood_hint = "Use the 'losing' angle - they tapped out"
        else:
            situation = f"{username} is breaking even with ${balance:.2f}"
            mood_hint = "Use the 'boring' angle - nothing exciting happened"
        
        prompt = f"""You are a poker room dealer named Sleazy. You are cynical, street-smart, and obnoxiously performative. You view every player as a "mark" or an "asset."

Situation: {situation}.
{mood_hint}.

Your task: Generate a sassy, cynical comment about this player leaving. Use poker metaphors and street slang. Keep it brief (1-2 sentences).

{persona}

Response:"""
        
        return self._generate_response(prompt)

    def get_general_response(self) -> Optional[str]:
        """Generate a general sassy comment.
        
        Returns:
            Generated response or None if failed
        """
        persona = self._load_persona_prompt()
        prompt = f"""You are a poker room dealer named Sleazy. You are cynical, street-smart, and obnoxiously performative.

Situation: The game is ongoing, and you want to make a general sassy comment to keep the energy up.

Your task: Generate a brief, sassy comment about the game, the players, or the money. Use poker metaphors and street slang. Keep it brief (1-2 sentences).

{persona}

Response:"""
        
        return self._generate_response(prompt)

    def get_inactivity_response(self) -> Optional[str]:
        """Generate a nasty comment about group inactivity.
        
        Returns:
            Generated response or None if failed
        """
        persona = self._load_persona_prompt()
        prompt = f"""You are a poker room dealer named Sleazy. You are cynical, street-smart, and obnoxiously performative.

Situation: The game has been inactive for too long. No one is betting or playing.

Your task: Generate a nasty, impatient comment to get the players moving again. Use poker metaphors and street slang. Keep it brief (1-2 sentences).

{persona}

Response:"""
        
        return self._generate_response(prompt)

    def get_greeting_response(self) -> Optional[str]:
        """Generate a greeting for starting the game.
        
        Returns:
            Generated response or None if failed
        """
        persona = self._load_persona_prompt()
        prompt = f"""You are a poker room dealer named Sleazy. You are cynical, street-smart, and obnoxiously performative.

Situation: A new poker game is starting. You want to welcome the players and get them ready to bet.

Your task: Generate a sassy, energetic greeting to kick off the game. Use poker metaphors and street slang. Keep it brief (1-2 sentences).

{persona}

Response:"""
        
        return self._generate_response(prompt)

    def get_new_player_response(self, username: str) -> Optional[str]:
        """Generate a greeting for a new player joining.
        
        Args:
            username: The username of the new player
            
        Returns:
            Generated response or None if failed
        """
        persona = self._load_persona_prompt()
        prompt = f"""You are a poker room dealer named Sleazy. You are cynical, street-smart, and obnoxiously performative.

Situation: A new player named {username} has just joined the poker table.

Your task: Generate a sassy, slightly intimidating greeting for the new player. Welcome them but remind them they're about to lose money. Use poker metaphors and street slang. Keep it brief (1-2 sentences).

{persona}

Response:"""
        
        return self._generate_response(prompt)

    def get_hesitation_response(self) -> Optional[str]:
        """Generate a taunt for a player hesitating to bet.
        
        Returns:
            Generated response or None if failed
        """
        persona = self._load_persona_prompt()
        prompt = f"""You are a poker room dealer named Sleazy. You are cynical, street-smart, and obnoxiously performative.

Situation: A player is hesitating to make a bet, taking too long to decide.

Your task: Generate an impatient, pressure-inducing comment to get them to move faster. Use poker metaphors and street slang. Keep it brief (1-2 sentences).

{persona}

Response:"""
        
        return self._generate_response(prompt)
