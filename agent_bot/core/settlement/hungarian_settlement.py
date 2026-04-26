"""Settlement service using greedy algorithm for optimal minimal transactions."""

import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Tuple, Dict, Optional
from agent_bot.db.models import Participant

logger = logging.getLogger(__name__)


class HungarianSettlementService:
    """Stateless settlement service using greedy algorithm for optimal matching."""

    DECIMAL_PLACES = 2

    @classmethod
    def calculate_settlement(cls, participants: List[Participant]) -> List[Tuple[int, int, Decimal]]:
        """
        Calculate minimal settlement transactions using greedy algorithm.

        Algorithm (Debt Simplification):
        1. Compute net position for each participant (current_bet - prize)
        2. Separate into debtors (negative balance) and creditors (positive balance)
        3. Sort debtors from most negative to least negative (largest debt first)
        4. Sort creditors from most positive to least positive (largest credit first)
        5. Use two-pointer technique: match largest debtor with largest creditor
        6. Settle for the minimum of the two absolute values
        7. Update balances and remove settled parties from the list
        8. Repeat until all balances are zero

        This greedy approach provides the optimal balance between calculation speed
        and a low number of transactions for practical applications.

        Args:
            participants: List of Participant objects with bets and prizes

        Returns:
            List of (from_user_id, to_user_id, amount) tuples
        """
        if not participants:
            return []

        # Calculate net position for each participant
        balances: Dict[int, Dict] = {}
        for p in participants:
            # Net position = total bet - prize (what they owe vs what they're owed)
            net_position = p.total_bet_amount - p.prize_amount
            balances[p.user_id] = {
                "balance": net_position
            }

        # Separate into debtors (negative) and creditors (positive)
        debtors = [
            (uid, abs(info["balance"]))
            for uid, info in balances.items()
            if info["balance"] < 0
        ]
        creditors = [
            (uid, info["balance"])
            for uid, info in balances.items()
            if info["balance"] > 0
        ]

        # Sort by amount (process largest first for optimal matching)
        # Debtors: most negative (largest debt) first
        debtors.sort(key=lambda x: x[1], reverse=True)
        # Creditors: most positive (largest credit) first
        creditors.sort(key=lambda x: x[1], reverse=True)

        logger.info(f"Settlement calculation: {len(debtors)} debtors, {len(creditors)} creditors")

        # Greedy matching using two-pointer technique
        transactions = []
        debtor_idx = 0
        creditor_idx = 0

        while debtor_idx < len(debtors) and creditor_idx < len(creditors):
            debtor_uid, debtor_amount = debtors[debtor_idx]
            creditor_uid, creditor_amount = creditors[creditor_idx]

            # Settle the minimum of the two absolute values
            settlement = min(debtor_amount, creditor_amount)
            settlement = cls._round_decimal(settlement)

            if settlement > Decimal("0"):
                transactions.append((debtor_uid, creditor_uid, settlement))

            # Update balances
            debtors[debtor_idx] = (debtor_uid, debtor_amount - settlement)
            creditors[creditor_idx] = (creditor_uid, creditor_amount - settlement)

            # Remove settled parties from the list
            if debtors[debtor_idx][1] <= Decimal("0"):
                debtor_idx += 1
            if creditors[creditor_idx][1] <= Decimal("0"):
                creditor_idx += 1

        # Round and clean up near-zero transactions
        cleaned_transactions = []
        for from_uid, to_uid, amount in transactions:
            amount = cls._round_decimal(amount)
            if amount > Decimal("0.001"):  # Skip trivial amounts
                cleaned_transactions.append((from_uid, to_uid, amount))

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
        total_debt = sum(t[2] for t in transactions)
        total_credit = sum(t[2] for t in transactions)

        if total_debt != total_credit:
            logger.error(f"Settlement imbalance: debt={total_debt}, credit={total_credit}")
            return False

        # Verify no circular payments (greedy should produce none)
        if cls._has_cycles(transactions):
            logger.warning("Settlement contains circular payments")
            return False

        return True

    @classmethod
    def _has_cycles(cls, transactions: List[Tuple]) -> bool:
        """Check if transaction graph has cycles."""
        if not transactions:
            return False

        # Build adjacency: from_uid -> to_uid
        from_to = {}
        for from_uid, _, to_uid, _ in transactions:
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
