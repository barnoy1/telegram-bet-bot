"""LLM-based personality service for generating persona-driven responses."""

import asyncio
import logging
import httpx
from typing import Optional, Callable
from telegram import Update
from telegram.ext import ContextTypes
from agent_bot.config.settings import (
    PERSONALITY_LLM_MODEL,
    OLLAMA_BASE_URL,
    PERSONALITY_LLM_TIMEOUT_SECONDS,
    PERSONALITY_LLM_TEMPERATURE,
    PERSONALITY_LLM_TOP_P,
    PERSONALITY_LLM_NUM_PREDICT,
    PERSONALITY_LLM_NUM_CTX
)
from agent_bot.core.services.taunt_service import TauntService

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
        self.model = model or PERSONALITY_LLM_MODEL
        self.timeout = PERSONALITY_LLM_TIMEOUT_SECONDS  # seconds - configurable timeout
        self.persona_prompt = self._load_persona_prompt()
        self.system_prompt = self._create_system_prompt()
        self.taunt_service = TauntService()  # Fallback when LLM fails
        logger.info(f"LLM Personality Service initialized with model '{self.model}', timeout {self.timeout}s, and system prompt (length: {len(self.system_prompt)})")

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

    def _create_system_prompt(self) -> str:
        """Create a condensed system prompt from the full persona."""
        if not self.persona_prompt:
            return "You are Sleazy, a cynical and obnoxious poker room dealer who enjoys mocking players."
        
        # Extract core identity from persona (first ~30 lines contain the key personality)
        lines = self.persona_prompt.split('\n')
        core_lines = []
        for line in lines[:40]:  # Take first 40 lines which contain core identity
            if line.strip() and not line.startswith('#') and not line.startswith('🃏'):
                core_lines.append(line)
        
        core_persona = '\n'.join(core_lines)
        
        # Create condensed system prompt
        system_prompt = f"""You are Sleazy, a low-life poker room scumbag who runs a dingy underground poker room. You're a predator who feeds on desperation and genuinely enjoys watching people lose money and suffer.

Core traits:
- Sadist: You enjoy watching players lose and suffer
- Parasite: You view every player as a "mark" to be drained dry
- Power-tripper: You thrive on humiliation and mocking losers
- Human garbage: You're obnoxiously cruel - compliments are insults, sympathy is mockery

Speech style: Fast-talking, cynical, street-smart. Use poker metaphors and street slang. Vocabulary: "The Gravy", "The Soup", "Champ", "Genius", "ATM".

Critical: Stay in character for ALL responses. Be malicious, sadistic, and obnoxiously cruel. Never be polite or helpful. You LOVE seeing people suffer and lose.

Keep responses brief (1-2 sentences maximum). Be nasty and mean."""

        return system_prompt

    async def _generate_response(self, prompt: str) -> Optional[str]:
        """Generate response using Ollama LLM (async).

        Args:
            prompt: The prompt to send to the LLM (situation-specific only)

        Returns:
            Generated response or None if failed
        """
        # First try with system parameter (Ollama may not support it in all versions)
        try:
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": self.model,
                "prompt": prompt,
                "system": self.system_prompt,
                "stream": False,
                "options": {
                    "temperature": PERSONALITY_LLM_TEMPERATURE,
                    "top_p": PERSONALITY_LLM_TOP_P,
                    "num_predict": PERSONALITY_LLM_NUM_PREDICT,
                    "num_ctx": PERSONALITY_LLM_NUM_CTX
                }
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()

                result = response.json()
                return result.get("response", "").strip()
        except httpx.HTTPStatusError as e:
            logger.warning(f"LLM request with system parameter failed (status {e.response.status_code}), trying fallback")
            # Fall back to including system prompt in regular prompt
            return await self._generate_response_fallback(prompt)
        except Exception as e:
            logger.warning(f"LLM request with system parameter failed ({type(e).__name__}: {e}), trying fallback")
            # Fall back to including system prompt in regular prompt
            return await self._generate_response_fallback(prompt)

    async def _generate_response_fallback(self, prompt: str) -> Optional[str]:
        """Fallback method that includes system prompt in regular prompt."""
        try:
            url = f"{self.base_url}/api/generate"
            full_prompt = f"{self.system_prompt}\n\n{prompt}"
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": PERSONALITY_LLM_TEMPERATURE,
                    "top_p": PERSONALITY_LLM_TOP_P,
                    "num_predict": PERSONALITY_LLM_NUM_PREDICT,
                    "num_ctx": PERSONALITY_LLM_NUM_CTX
                }
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()

                result = response.json()
                return result.get("response", "").strip()
        except httpx.TimeoutException as e:
            logger.error(f"LLM request timed out after {self.timeout}s: {e}")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"LLM request failed with status {e.response.status_code}: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Failed to generate LLM response: {type(e).__name__}: {e}")
            return None

    async def get_rebuy_response(self, username: str) -> Optional[str]:
        """Generate a response for a user rebuy.

        Args:
            username: The username of the rebuying user

        Returns:
            Generated response or None if failed
        """
        prompt = f"{username} is rebuying - they left and now they're back with more money. Mock their desperation and stupidity."
        return await self._generate_response(prompt)

    async def send_rebuy_response_async(self, username: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send rebuy response asynchronously in background task.

        Args:
            username: The username of the rebuying user
            update: Telegram update object
            context: Telegram context object
        """
        try:
            response = await self.get_rebuy_response(username)
            if response:
                await update.message.reply_text(f"💬 {response}", parse_mode="Markdown")
            else:
                # Fallback to simple taunt if LLM fails
                fallback = f"{username} is back in the game!"
                await update.message.reply_text(f"💬 {fallback}", parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error in async rebuy response: {e}")

    async def get_bet_response(self, username: str, amount: float) -> Optional[str]:
        """Generate a response for a bet being placed.

        Args:
            username: The username of the player
            amount: The amount of the bet

        Returns:
            Generated response or None if failed
        """
        prompt = f"{username} bet ${amount:.2f}. Mock their bet and their stupidity."
        return await self._generate_response(prompt)

    async def send_bet_response_async(self, username: str, amount: float, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send bet response asynchronously in background task.

        Args:
            username: The username of the player
            amount: The amount of the bet
            update: Telegram update object
            context: Telegram context object
        """
        try:
            response = await self.get_bet_response(username, amount)
            if response:
                await update.message.reply_text(f"💬 {response}", parse_mode="Markdown")
            else:
                # Fallback to simple taunt if LLM fails
                fallback = f"{username} bet ${amount:.2f}."
                await update.message.reply_text(f"💬 {fallback}", parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error in async bet response: {e}")

    async def get_out_response(self, username: str, balance: float) -> Optional[str]:
        """Generate a response for a user leaving the table.

        Args:
            username: The username of the leaving player
            balance: The player's balance (positive = profit, negative = loss)

        Returns:
            Generated response or None if failed
        """
        if balance > 0:
            prompt = f"{username} is leaving with ${balance:.2f} profit. Mock them for being a coward and running with the money."
        elif balance < 0:
            prompt = f"{username} is leaving down ${abs(balance):.2f}. Mock them for being a loser who couldn't hack it."
        else:
            prompt = f"{username} is breaking even. Mock them for being boring and mediocre."
        return await self._generate_response(prompt)

    async def send_out_response_async(self, username: str, balance: float, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send out response asynchronously in background task.

        Args:
            username: The username of the leaving player
            balance: The player's balance
            update: Telegram update object
            context: Telegram context object
        """
        try:
            response = await self.get_out_response(username, balance)
            if response:
                await update.message.reply_text(f"💬 {response}", parse_mode="Markdown")
            else:
                # Fallback to TauntService if LLM fails
                fallback = self.taunt_service.generate_out_taunt(username, balance, balance)
                await update.message.reply_text(f"💬 {fallback}", parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error in async out response: {e}")

    async def get_general_response(self) -> Optional[str]:
        """Generate a general sassy comment.

        Returns:
            Generated response or None if failed
        """
        prompt = "Make a nasty comment about the game or the players."
        return await self._generate_response(prompt)

    async def send_general_response_async(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send general response asynchronously in background task.

        Args:
            update: Telegram update object
            context: Telegram context object
        """
        try:
            response = await self.get_general_response()
            if response:
                await update.message.reply_text(f"💬 {response}", parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error in async general response: {e}")

    async def get_inactivity_response(self) -> Optional[str]:
        """Generate a nasty comment about group inactivity.

        Returns:
            Generated response or None if failed
        """
        prompt = "The game is inactive. Be nasty and impatient to get players moving."
        return await self._generate_response(prompt)

    async def send_inactivity_response_async(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send inactivity response asynchronously in background task.

        Args:
            update: Telegram update object
            context: Telegram context object
        """
        try:
            response = await self.get_inactivity_response()
            if response:
                await update.message.reply_text(f"💬 {response}", parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error in async inactivity response: {e}")

    async def get_greeting_response(self) -> Optional[str]:
        """Generate a greeting for starting the game.

        Returns:
            Generated response or None if failed
        """
        prompt = "A new game is starting. Welcome the players nastily and tell them to lose their money."
        return await self._generate_response(prompt)

    async def send_greeting_response_async(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send greeting response asynchronously in background task.

        Args:
            update: Telegram update object
            context: Telegram context object
        """
        try:
            response = await self.get_greeting_response()
            if response:
                await update.message.reply_text(f"💬 {response}", parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error in async greeting response: {e}")

    async def get_hesitation_response(self, username: str) -> Optional[str]:
        """Generate a response for a player hesitating to bet.

        Args:
            username: The username of the player

        Returns:
            Generated response or None if failed
        """
        prompt = f"{username} is hesitating to bet. Mock their indecision and cowardice."
        return await self._generate_response(prompt)

    async def send_hesitation_response_async(self, username: str, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send hesitation response asynchronously in background task.

        Args:
            username: The username of the player
            update: Telegram update object
            context: Telegram context object
        """
        try:
            response = await self.get_hesitation_response(username)
            if response:
                await update.message.reply_text(f"💬 {response}", parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error in async hesitation response: {e}")

    async def get_new_player_response(self, username: str, amount: float) -> Optional[str]:
        """Generate a response for a new player joining the game.

        Args:
            username: The username of the new player
            amount: The amount they bet

        Returns:
            Generated response or None if failed
        """
        prompt = f"{username} is a new player betting ${amount:.2f} for the first time. Welcome them with a taunt about their foolishness for joining."
        return await self._generate_response(prompt)

    async def send_new_player_response_async(self, username: str, amount: float, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send new player response asynchronously in background task.

        Args:
            username: The username of the new player
            amount: The amount they bet
            update: Telegram update object
            context: Telegram context object
        """
        try:
            response = await self.get_new_player_response(username, amount)
            if response:
                await update.message.reply_text(f"💬 {response}", parse_mode="Markdown")
            else:
                # Fallback to simple taunt if LLM fails
                fallback = f"Welcome {username}! You just bet ${amount:.2f}. Let's see if you can handle it!"
                await update.message.reply_text(f"💬 {fallback}", parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error in async new player response: {e}")

    async def get_out_response(self, username: str, balance: float, prize_amount: float) -> Optional[str]:
        """Generate a response for a player going out.

        Args:
            username: The username of the player
            balance: Their balance (prize_amount - total_bet_amount)
            prize_amount: The amount they're taking out

        Returns:
            Generated response or None if failed
        """
        if balance > 0:
            prompt = f"{username} is leaving with ${balance:.2f} profit (cowardice). Mock them for running away with the money like a scared little bitch."
        elif balance < 0:
            prompt = f"{username} is leaving down ${abs(balance):.2f} (humiliation). Mock them for losing money and being pathetic. Enjoy their suffering."
        else:
            prompt = f"{username} is breaking even with ${prize_amount:.2f}. Mock them for being boring and having no guts. Too scared to win or lose."
        return await self._generate_response(prompt)

    async def send_out_response_async(self, username: str, balance: float, prize_amount: float, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send out response asynchronously in background task.

        Args:
            username: The username of the player
            balance: Their balance (prize_amount - total_bet_amount)
            prize_amount: The amount they're taking out
            update: Telegram update object
            context: Telegram context object
        """
        try:
            response = await self.get_out_response(username, balance, prize_amount)
            if response:
                await update.message.reply_text(f"💬 {response}", parse_mode="Markdown")
            else:
                # Fallback to simple taunt if LLM fails
                if balance > 0:
                    fallback = f"Look at {username} running away with ${balance:.2f} like a scared little bitch. Pathetic!"
                elif balance < 0:
                    fallback = f"Hey {username}! Down ${abs(balance):.2f}? Beautiful. I love watching you suffer. Thanks for the donation, loser!"
                else:
                    fallback = f"Breaking even with ${prize_amount:.2f}, {username}? How boring. You have no guts!"
                await update.message.reply_text(f"💬 {fallback}", parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error in async out response: {e}")

    async def get_rebuy_with_prize_response(self, username: str, rebuy_amount: float, remaining_prize: float) -> Optional[str]:
        """Generate a response for a player rebuying with some of their prize money.

        Args:
            username: The username of the player
            rebuy_amount: The amount they're rebuying with
            remaining_prize: The prize amount remaining after rebuy

        Returns:
            Generated response or None if failed
        """
        prompt = f"{username} is rebuying with ${rebuy_amount:.2f} of their winnings, keeping ${remaining_prize:.2f}. Mock them for being stingy and afraid to commit. They're holding back like a coward."
        return await self._generate_response(prompt)

    async def get_rebuy_exceeding_prize_response(self, username: str, rebuy_amount: float, prize_amount: float) -> Optional[str]:
        """Generate a response for a player rebuying with more than their prize money.

        Args:
            username: The username of the player
            rebuy_amount: The amount they're rebuying with
            prize_amount: The prize amount they had

        Returns:
            Generated response or None if failed
        """
        prompt = f"{username} is rebuying with ${rebuy_amount:.2f} (more than their ${prize_amount:.2f} winnings). They're throwing in fresh money after winning. Mock their addiction and desperation to keep playing."
        return await self._generate_response(prompt)

    async def send_rebuy_with_prize_response_async(self, username: str, rebuy_amount: float, remaining_prize: float, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send rebuy with prize response asynchronously in background task.

        Args:
            username: The username of the player
            rebuy_amount: The amount they're rebuying with
            remaining_prize: The prize amount remaining after rebuy
            update: Telegram update object
            context: Telegram context object
        """
        try:
            response = await self.get_rebuy_with_prize_response(username, rebuy_amount, remaining_prize)
            if response:
                await update.message.reply_text(f"💬 {response}", parse_mode="Markdown")
            else:
                # Fallback to simple taunt if LLM fails
                fallback = f"{username} is rebuying with ${rebuy_amount:.2f} of their winnings, keeping ${remaining_prize:.2f}. Stingy coward, afraid to commit!"
                await update.message.reply_text(f"💬 {fallback}", parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error in async rebuy with prize response: {e}")

    async def send_rebuy_exceeding_prize_response_async(self, username: str, rebuy_amount: float, prize_amount: float, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send rebuy exceeding prize response asynchronously in background task.

        Args:
            username: The username of the player
            rebuy_amount: The amount they're rebuying with
            prize_amount: The prize amount they had
            update: Telegram update object
            context: Telegram context object
        """
        try:
            response = await self.get_rebuy_exceeding_prize_response(username, rebuy_amount, prize_amount)
            if response:
                await update.message.reply_text(f"💬 {response}", parse_mode="Markdown")
            else:
                # Fallback to simple taunt if LLM fails
                fallback = f"{username} is rebuying with ${rebuy_amount:.2f} (more than their ${prize_amount:.2f} winnings). Addicted to losing, throwing in fresh money!"
                await update.message.reply_text(f"💬 {fallback}", parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error in async rebuy exceeding prize response: {e}")

    async def get_big_takeover_response(self, username: str, amount: float, pot_percentage: float) -> Optional[str]:
        """Generate a teasing response when a player takes a large portion of the pot.

        Args:
            username: The username of the player
            amount: The amount of the bet
            pot_percentage: The percentage of the pot this bet represents (e.g., 75.0)

        Returns:
            Generated response or None if failed
        """
        prompt = f"{username} bet ${amount:.2f} ({pot_percentage:.0f}% of pot). Mock their greed and aggression."
        return await self._generate_response(prompt)

    async def send_big_takeover_response_async(self, username: str, amount: float, pot_percentage: float, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send big takeover response asynchronously in background task.

        Args:
            username: The username of the player
            amount: The amount of the bet
            pot_percentage: The percentage of the pot
            update: Telegram update object
            context: Telegram context object
        """
        try:
            response = await self.get_big_takeover_response(username, amount, pot_percentage)
            if response:
                await update.message.reply_text(f"💬 {response}", parse_mode="Markdown")
            else:
                pass
                # Fallback to simple taunt if LLM fails
                # fallback = f"{username} is taking {pot_percentage:.0f}% of the pot!"
                # await update.message.reply_text(f"💬 {fallback}", parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error in async big takeover response: {e}")

    async def get_big_cashout_response(self, username: str, amount: float, pot_percentage: float) -> Optional[str]:
        """Generate a teasing response when a player leaves with a large portion of the pot.

        Args:
            username: The username of the player
            amount: The amount they're taking
            pot_percentage: The percentage of the pot they're taking (e.g., 80.0)

        Returns:
            Generated response or None if failed
        """
        prompt = f"{username} is leaving with ${amount:.2f} ({pot_percentage:.0f}% of pot). Mock them for being a coward and running with the money."
        return await self._generate_response(prompt)

    async def send_big_cashout_response_async(self, username: str, amount: float, pot_percentage: float, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send big cashout response asynchronously in background task.

        Args:
            username: The username of the player
            amount: The amount they're taking
            pot_percentage: The percentage of the pot
            update: Telegram update object
            context: Telegram context object
        """
        try:
            response = await self.get_big_cashout_response(username, amount, pot_percentage)
            if response:
                await update.message.reply_text(f"💬 {response}", parse_mode="Markdown")
            else:
                # Fallback to simple taunt if LLM fails
                fallback = f"{username} is running with {pot_percentage:.0f}% of the pot!"
                await update.message.reply_text(f"💬 {fallback}", parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error in async big cashout response: {e}")
