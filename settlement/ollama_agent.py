"""Ollama LLM integration for settlement reasoning."""

import asyncio
import json
import logging
import httpx
from decimal import Decimal
from typing import List, Tuple, Optional, Dict
from db.storage import Participant
from config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)


class OllamaSettlementAgent:
    """
    Uses Ollama (local LLM) for settlement reasoning.
    Fallback to deterministic calculator if Ollama unavailable.
    """

    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = OLLAMA_MODEL, timeout: int = OLLAMA_TIMEOUT_SECONDS):
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self._initialized = False

    async def initialize(self) -> bool:
        """Check if Ollama is available."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    model_names = [m.get("name") for m in models]
                    if self.model in model_names or any(self.model in m for m in model_names):
                        self._initialized = True
                        logger.info(f"Ollama initialized with model: {self.model}")
                        return True
                    else:
                        logger.warning(f"Model {self.model} not found in Ollama. Available: {model_names}")
                        return False
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            return False

    async def calculate_settlement(
        self, participants: List[Participant]
    ) -> Optional[List[Tuple[int, str, int, str, Decimal]]]:
        """
        Use Ollama to reason about settlement.

        Args:
            participants: List of Participant objects with bets and prizes

        Returns:
            List of settlement transactions, or None if Ollama fails
        """
        if not self._initialized:
            return None

        try:
            # Prepare prompt for Ollama
            bets_dict = {p.user_id: float(p.bet_amount) for p in participants}
            winners_dict = {p.user_id: float(p.prize_amount) for p in participants if p.is_winner}
            usernames = {p.user_id: p.username for p in participants}

            prompt = self._build_settlement_prompt(bets_dict, winners_dict, usernames)

            # Call Ollama API
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={"model": self.model, "prompt": prompt, "stream": False},
                )

                if response.status_code != 200:
                    logger.warning(f"Ollama returned {response.status_code}")
                    return None

                result = response.json()
                response_text = result.get("response", "")

            # Parse Ollama response
            transactions = self._parse_settlement_response(response_text, usernames)
            if transactions is not None:
                logger.info(f"Ollama generated {len(transactions)} settlement transactions")
            return transactions

        except asyncio.TimeoutError:
            logger.warning(f"Ollama timeout after {self.timeout}s")
            return None
        except Exception as e:
            logger.warning(f"Ollama settlement failed: {e}")
            return None

    def _build_settlement_prompt(
        self, bets: Dict[int, float], winners: Dict[int, float], usernames: Dict[int, str]
    ) -> str:
        """Build a structured prompt for settlement reasoning."""
        participants_str = "\n".join(
            f"- User {uid} ({usernames[uid]}): bet ${bets[uid]:.2f}"
            for uid in sorted(bets.keys())
        )

        winners_str = "\n".join(
            f"- User {uid} ({usernames[uid]}): won ${winners[uid]:.2f}"
            for uid in sorted(winners.keys())
        ) if winners else "None"

        return f"""You are a settlement calculator for a betting group.

Participants and their bets:
{participants_str}

Winners and their prizes:
{winners_str}

Your task:
1. Calculate each participant's net position (prize - bet)
2. Identify debtors (negative balance) and creditors (positive balance)
3. Generate minimal settlement transactions (debtor pays creditor)
4. Output ONLY a JSON array with no markdown, no explanation.

Format:
```json
[
  {{"from_user_id": <int>, "to_user_id": <int>, "amount": <float>}},
  ...
]
```

Ensure:
- No circular payments (A→B→C→A)
- All debts are settled exactly
- Amount is rounded to 2 decimal places
- If all participants break even, return empty array []

Output ONLY the JSON, nothing else."""

    def _parse_settlement_response(
        self, response: str, usernames: Dict[int, str]
    ) -> Optional[List[Tuple[int, str, int, str, Decimal]]]:
        """Parse JSON response from Ollama."""
        try:
            # Extract JSON from response (may be wrapped in markdown)
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()

            transactions_json = json.loads(json_str)

            # Convert to internal format
            transactions = []
            for tx in transactions_json:
                from_uid = int(tx["from_user_id"])
                to_uid = int(tx["to_user_id"])
                amount = Decimal(str(tx["amount"]))

                from_name = usernames.get(from_uid, f"User{from_uid}")
                to_name = usernames.get(to_uid, f"User{to_uid}")

                transactions.append((from_uid, from_name, to_uid, to_name, amount))

            return transactions
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse Ollama response: {e}")
            logger.debug(f"Response was: {response}")
            return None
