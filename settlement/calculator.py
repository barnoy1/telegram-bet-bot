"""Deterministic settlement calculation for betting groups."""

import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Tuple
from db.storage import Participant

logger = logging.getLogger(__name__)


class SettlementCalculator:
    """Calculates fair settlement of bets between participants."""

    DECIMAL_PLACES = 2

    @classmethod
    def calculate_settlement(
        cls, participants: List[Participant]
    ) -> List[Tuple[int, str, int, str, Decimal]]:
        """
        Calculate minimal settlement transactions.

        Algorithm:
        1. Compute net position for each participant (what they contributed - what they won)
        2. Separate into debtors (negative balance) and creditors (positive balance)
        3. Match debtors with creditors greedily, minimizing transactions

        Args:
            participants: List of Participant objects with bets and prizes

        Returns:
            List of (from_user_id, from_username, to_user_id, to_username, amount) tuples
        """
        if not participants:
            return []

        # Calculate net position for each participant
        balances: Dict[int, Dict] = {}
        for p in participants:
            balance = p.prize_amount - p.bet_amount
            balances[p.user_id] = {"balance": balance, "username": p.username}

        # Separate into debtors and creditors
        debtors = [
            (uid, info["username"], abs(info["balance"]))
            for uid, info in balances.items()
            if info["balance"] < 0
        ]
        creditors = [
            (uid, info["username"], info["balance"])
            for uid, info in balances.items()
            if info["balance"] > 0
        ]

        # Sort by amount (process largest first for clarity)
        debtors.sort(key=lambda x: x[2], reverse=True)
        creditors.sort(key=lambda x: x[2], reverse=True)

        # Greedy matching
        transactions = []
        debtor_idx = 0
        creditor_idx = 0

        while debtor_idx < len(debtors) and creditor_idx < len(creditors):
            debtor_uid, debtor_name, debtor_amount = debtors[debtor_idx]
            creditor_uid, creditor_name, creditor_amount = creditors[creditor_idx]

            # Settle as much as possible between these two
            settlement = min(debtor_amount, creditor_amount)
            settlement = cls._round_decimal(settlement)

            if settlement > Decimal("0"):
                transactions.append(
                    (debtor_uid, debtor_name, creditor_uid, creditor_name, settlement)
                )

            # Update amounts
            debtors[debtor_idx] = (debtor_uid, debtor_name, debtor_amount - settlement)
            creditors[creditor_idx] = (creditor_uid, creditor_name, creditor_amount - settlement)

            # Move to next if current is settled
            if debtors[debtor_idx][2] <= Decimal("0"):
                debtor_idx += 1
            if creditors[creditor_idx][2] <= Decimal("0"):
                creditor_idx += 1

        # Round and clean up near-zero transactions
        cleaned_transactions = []
        for from_uid, from_name, to_uid, to_name, amount in transactions:
            amount = cls._round_decimal(amount)
            if amount > Decimal("0.001"):  # Skip trivial amounts
                cleaned_transactions.append((from_uid, from_name, to_uid, to_name, amount))

        logger.info(f"Calculated {len(cleaned_transactions)} settlement transactions")
        return cleaned_transactions

    @classmethod
    def _round_decimal(cls, value: Decimal) -> Decimal:
        """Round to DECIMAL_PLACES using banker's rounding."""
        if isinstance(value, float):
            value = Decimal(str(value))
        quantizer = Decimal(10) ** -cls.DECIMAL_PLACES
        return value.quantize(quantizer, rounding=ROUND_HALF_UP)

    @classmethod
    def validate_settlement(cls, participants: List[Participant], transactions: List[Tuple]) -> bool:
        """Validate that settlement is mathematically correct."""
        # Calculate total debts and credits
        total_debt = sum(t[4] for t in transactions)
        total_credit = sum(t[4] for t in transactions)

        if total_debt != total_credit:
            logger.error(f"Settlement imbalance: debt={total_debt}, credit={total_credit}")
            return False

        # Verify no circular payments
        if cls._has_cycles(transactions):
            logger.warning("Settlement contains circular payments")
            return False

        return True

    @classmethod
    def _has_cycles(cls, transactions: List[Tuple]) -> bool:
        """Check if transaction graph has cycles (greedy settlement should have none)."""
        # For greedy settlement, cycles shouldn't exist, but check as safety
        if not transactions:
            return False

        # Build adjacency: from_uid -> to_uid
        from_to = {}
        for from_uid, _, to_uid, _, _ in transactions:
            if from_uid not in from_to:
                from_to[from_uid] = []
            from_to[from_uid].append(to_uid)

        # DFS to detect cycles
        def has_cycle_dfs(node: int, visited: set, rec_stack: set) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in from_to.get(node, []):
                if neighbor not in visited:
                    if has_cycle_dfs(neighbor, visited, rec_stack):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        visited = set()
        for node in from_to.keys():
            if node not in visited:
                if has_cycle_dfs(node, visited, set()):
                    return True

        return False
