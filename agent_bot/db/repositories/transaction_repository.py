"""Transaction repository for database operations."""

from typing import List
from sqlalchemy.orm import Session

from agent_bot.db.models import Transaction, TransactionModel
from agent_bot.db.repositories.base_repository import BaseRepository


class TransactionRepository(BaseRepository):
    """Repository for transaction-related database operations."""

    def create_transaction(self, event_id: int, from_user_id: int, to_user_id: int, amount) -> Transaction:
        """Create a new transaction."""
        new_transaction = TransactionModel(
            event_id=event_id,
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            amount=amount
        )
        self.session.add(new_transaction)
        self.commit()
        self.session.refresh(new_transaction)
        return self._model_to_dataclass(new_transaction, Transaction)

    def get_transactions(self, event_id: int) -> List[Transaction]:
        """Get all transactions for an event."""
        transactions = self.session.query(TransactionModel).filter(
            TransactionModel.event_id == event_id
        ).all()
        return [self._model_to_dataclass(t, Transaction) for t in transactions]

    def delete_transactions(self, event_id: int) -> bool:
        """Delete all transactions for an event."""
        from sqlalchemy import delete
        result = self.session.execute(
            delete(TransactionModel).where(TransactionModel.event_id == event_id)
        )
        self.commit()
        return result.rowcount > 0
