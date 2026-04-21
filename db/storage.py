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
    prize_amount: Decimal = Decimal("0")
    status: str = "in"
    settlement_timestamp: Optional[str] = None


@dataclass
class BettingGroup:
    """Represents a betting group."""
    group_id: int
    group_name: str
    creator_id: int
    created_at: str
    last_activity_timestamp: Optional[str] = None


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
                    settled_at TIMESTAMP,
                    last_activity_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            
            # Add last_activity_timestamp column if it doesn't exist (migration)
            cursor.execute("PRAGMA table_info(groups)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'last_activity_timestamp' not in columns:
                cursor.execute(
                    "ALTER TABLE groups ADD COLUMN last_activity_timestamp TIMESTAMP"
                )
                # Update existing rows with current timestamp
                cursor.execute(
                    "UPDATE groups SET last_activity_timestamp = CURRENT_TIMESTAMP WHERE last_activity_timestamp IS NULL"
                )
                logger.info("Added last_activity_timestamp column to groups table")

            # Participants table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS participants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    username TEXT NOT NULL,
                    bet_amount REAL NOT NULL CHECK(bet_amount >= 0),
                    prize_amount REAL DEFAULT 0,
                    status TEXT DEFAULT 'in' CHECK(status IN ('in', 'out')),
                    settlement_timestamp TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (group_id) REFERENCES groups(group_id),
                    UNIQUE(group_id, user_id)
                )
                """
            )
            
            # Add status column to participants table if it doesn't exist (migration)
            cursor.execute("PRAGMA table_info(participants)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'status' not in columns:
                cursor.execute(
                    "ALTER TABLE participants ADD COLUMN status TEXT DEFAULT 'in'"
                )
                logger.info("Added status column to participants table")
            
            # Add settlement_timestamp column to participants table if it doesn't exist (migration)
            cursor.execute("PRAGMA table_info(participants)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'settlement_timestamp' not in columns:
                cursor.execute(
                    "ALTER TABLE participants ADD COLUMN settlement_timestamp TIMESTAMP"
                )
                logger.info("Added settlement_timestamp column to participants table")

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
                "SELECT group_id, group_name, creator_id, created_at, last_activity_timestamp FROM groups WHERE group_id = ?",
                (group_id,),
            )
            row = cursor.fetchone()
            if row:
                return BettingGroup(*row)
        return None

    def get_all_groups(self) -> List[BettingGroup]:
        """Retrieve all groups."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT group_id, group_name, creator_id, created_at, last_activity_timestamp FROM groups"
            )
            return [
                BettingGroup(*row)
                for row in cursor.fetchall()
            ]

    def update_group_activity(self, group_id: int, activity_time: datetime) -> bool:
        """Update the last activity timestamp for a group."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE groups SET last_activity_timestamp = ? WHERE group_id = ?",
                    (activity_time.isoformat(), group_id),
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating group activity: {e}")
            return False

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
                SELECT user_id, username, bet_amount, prize_amount, status, settlement_timestamp
                FROM participants WHERE group_id = ? ORDER BY user_id
                """,
                (group_id,),
            )
            return [
                Participant(int(row[0]), row[1], Decimal(str(row[2])), Decimal(str(row[3])), row[4], row[5])
                for row in cursor.fetchall()
            ]

    def set_user_out(self, group_id: int, user_id: int, prize_amount: Decimal) -> bool:
        """Mark user as 'out' with prize amount and update settlement timestamp."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE participants
                    SET prize_amount = ?, status = 'out', settlement_timestamp = CURRENT_TIMESTAMP
                    WHERE group_id = ? AND user_id = ?
                    """,
                    (float(prize_amount), group_id, user_id),
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error setting user out: {e}")
            return False

    def get_total_pot(self, group_id: int) -> Decimal:
        """Get total pot for a group."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT SUM(bet_amount) FROM participants WHERE group_id = ? AND status = 'in'",
                (group_id,),
            )
            result = cursor.fetchone()
            if result and result[0]:
                return Decimal(str(result[0]))
            return Decimal("0")

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
