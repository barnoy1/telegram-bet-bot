"""Copilot SDK integration for settlement reasoning."""

import asyncio
import json
import logging
from decimal import Decimal
from typing import List, Tuple, Optional, Dict
from db.storage import Participant

logger = logging.getLogger(__name__)


class CopilotSettlementAgent:
    """
    Wrapper around Copilot SDK for settlement logic.
    Falls back to deterministic calculator if Copilot unavailable.
    """

    def __init__(self, cli_path: str = "copilot", timeout: int = 30):
        self.cli_path = cli_path
        self.timeout = timeout
        self.client = None
        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize Copilot client. Returns False if unavailable."""
        try:
            # Attempt lazy import of copilot SDK
            from copilot import CopilotClient

            self.client = CopilotClient()
            self._initialized = True
            logger.info("Copilot client initialized successfully")
            return True
        except ImportError:
            logger.warning("Copilot SDK not available; using deterministic fallback")
            return False
        except Exception as e:
            logger.warning(f"Copilot initialization failed: {e}; using fallback")
            return False

    async def calculate_settlement(
        self, participants: List[Participant]
    ) -> Optional[List[Tuple[int, str, int, str, Decimal]]]:
        """
        Use Copilot agent to reason about settlement.

        Args:
            participants: List of Participant objects with bets and prizes

        Returns:
            List of settlement transactions, or None if Copilot fails
        """
        if not self._initialized or self.client is None:
            return None

        try:
            # Prepare prompt for Copilot agent
            bets_dict = {p.user_id: float(p.bet_amount) for p in participants}
            winners_dict = {p.user_id: float(p.prize_amount) for p in participants if p.is_winner}
            usernames = {p.user_id: p.username for p in participants}

            prompt = self._build_settlement_prompt(bets_dict, winners_dict, usernames)

            # Create session and send prompt
            session = await asyncio.wait_for(
                self.client.create_session(), timeout=self.timeout
            )
            reply = await asyncio.wait_for(
                session.send_and_wait({"prompt": prompt}), timeout=self.timeout
            )

            # Parse Copilot response
            transactions = self._parse_settlement_response(reply, usernames)
            logger.info(f"Copilot generated {len(transactions)} settlement transactions")
            return transactions

        except asyncio.TimeoutError:
            logger.warning(f"Copilot timeout after {self.timeout}s")
            return None
        except Exception as e:
            logger.warning(f"Copilot settlement failed: {e}")
            return None

    def _build_settlement_prompt(
        self, bets: Dict[int, float], winners: Dict[int, float], usernames: Dict[int, str]
    ) -> str:
        """Build a structured prompt for settlement reasoning."""
        participants_str = "\n".join(
            f"- User {uid} ({usernames[uid]}): bet ${bets[uid]:.2f}"
            for uid in bets.keys()
        )

        winners_str = "\n".join(
            f"- User {uid} ({usernames[uid]}): won ${winners[uid]:.2f}"
            for uid in winners.keys()
        ) if winners else "None"

        return f"""You are a settlement calculator for a betting group.

Participants and their bets:
{participants_str}

Winners and their prizes:
{winners_str}

Your task:
1. Calculate each participant's net position (prize - bet)
2. Identify debtors (negative) and creditors (positive)
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
    ) -> List[Tuple[int, str, int, str, Decimal]]:
        """Parse JSON response from Copilot."""
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
            logger.error(f"Failed to parse Copilot response: {e}")
            return None
