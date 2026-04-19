"""SQLite storage for betting groups, participants, and transactions."""

import sqlite3
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Participant:
    """Represents a betting group participant."""
    user_id: int
    username: str
    bet_amount: Decimal
    is_winner: bool = False
    prize_amount: Decimal = Decimal("0")
    status: str = "in"


@dataclass
class BettingGroup:
    """Represents a betting group."""
    group_id: int
    group_name: str
    creator_id: int
    created_at: str


class BettingStorage:
    """Manages SQLite database for betting groups and transactions."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Groups table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS groups (
                    group_id INTEGER PRIMARY KEY,
                    group_name TEXT NOT NULL,
                    creator_id INTEGER NOT NULL,
                    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'closed', 'settled')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    settled_at TIMESTAMP
                )
                """
            )

            # Participants table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS participants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    username TEXT NOT NULL,
                    bet_amount REAL NOT NULL CHECK(bet_amount >= 0),
                    is_winner INTEGER DEFAULT 0,
                    prize_amount REAL DEFAULT 0,
                    status TEXT DEFAULT 'in' CHECK(status IN ('in', 'out')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (group_id) REFERENCES groups(group_id),
                    UNIQUE(group_id, user_id)
                )
                """
            )

            # Transactions table (settlement results)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER NOT NULL,
                    from_user_id INTEGER NOT NULL,
                    from_username TEXT NOT NULL,
                    to_user_id INTEGER NOT NULL,
                    to_username TEXT NOT NULL,
                    amount REAL NOT NULL CHECK(amount > 0),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (group_id) REFERENCES groups(group_id)
                )
                """
            )

            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")

    def create_group(self, group_id: int, group_name: str, creator_id: int) -> BettingGroup:
        """Create a new betting group."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO groups (group_id, group_name, creator_id) VALUES (?, ?, ?)",
                (group_id, group_name, creator_id),
            )
            conn.commit()
        return BettingGroup(group_id, group_name, creator_id, datetime.now().isoformat())

    def get_group(self, group_id: int) -> Optional[BettingGroup]:
        """Retrieve a group by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT group_id, group_name, creator_id, created_at FROM groups WHERE group_id = ?",
                (group_id,),
            )
            row = cursor.fetchone()
            if row:
                return BettingGroup(*row)
        return None

    def add_participant(self, group_id: int, user_id: int, username: str, bet_amount: Decimal) -> bool:
        """Add or update a participant in a group. If user exists and is 'out', reset to 'in'."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO participants (group_id, user_id, username, bet_amount, status)
                    VALUES (?, ?, ?, ?, 'in')
                    ON CONFLICT(group_id, user_id) DO UPDATE SET
                        bet_amount = bet_amount + ?,
                        status = 'in'
                    """,
                    (group_id, user_id, username, float(bet_amount), float(bet_amount)),
                )
                conn.commit()
            return True
        except sqlite3.IntegrityError as e:
            logger.error(f"Error adding participant: {e}")
            return False

    def get_participants(self, group_id: int) -> List[Participant]:
        """Get all participants in a group."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT user_id, username, bet_amount, is_winner, prize_amount, status
                FROM participants WHERE group_id = ? ORDER BY user_id
                """,
                (group_id,),
            )
            return [
                Participant(int(row[0]), row[1], Decimal(str(row[2])), bool(row[3]), Decimal(str(row[4])), row[5])
                for row in cursor.fetchall()
            ]

    def set_winners(self, group_id: int, winners: Dict[int, Decimal]) -> bool:
        """Mark winners, set prize amounts, and mark user as 'out'."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for user_id, prize_amount in winners.items():
                    cursor.execute(
                        """
                        UPDATE participants
                        SET is_winner = 1, prize_amount = ?, status = 'out'
                        WHERE group_id = ? AND user_id = ?
                        """,
                        (float(prize_amount), group_id, user_id),
                    )
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error setting winners: {e}")
            return False

    def save_transactions(self, group_id: int, transactions: List[Tuple[int, str, int, str, Decimal]]) -> bool:
        """Save settlement transactions."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for from_user_id, from_username, to_user_id, to_username, amount in transactions:
                    cursor.execute(
                        """
                        INSERT INTO transactions
                        (group_id, from_user_id, from_username, to_user_id, to_username, amount)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (group_id, from_user_id, from_username, to_user_id, to_username, float(amount)),
                    )
                cursor.execute(
                    "UPDATE groups SET status = 'settled', settled_at = CURRENT_TIMESTAMP WHERE group_id = ?",
                    (group_id,),
                )
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving transactions: {e}")
            return False

    def get_transactions(self, group_id: int) -> List[Dict]:
        """Get all transactions for a group."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT from_user_id, from_username, to_user_id, to_username, amount
                FROM transactions WHERE group_id = ? ORDER BY id
                """,
                (group_id,),
            )
            return [
                {
                    "from_user_id": int(row[0]),
                    "from_username": row[1],
                    "to_user_id": int(row[2]),
                    "to_username": row[3],
                    "amount": Decimal(str(row[4])),
                }
                for row in cursor.fetchall()
            ]

    def delete_last_participant(self, group_id: int) -> bool:
        """Delete the last participant (most recent bet) in a group."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    DELETE FROM participants
                    WHERE id = (
                        SELECT id FROM participants
                        WHERE group_id = ?
                        ORDER BY id DESC
                        LIMIT 1
                    )
                    """,
                    (group_id,),
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting last participant: {e}")
            return False

    def delete_all_participants(self, group_id: int) -> bool:
        """Delete all participants in a group."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM participants WHERE group_id = ?", (group_id,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error deleting all participants: {e}")
            return False
