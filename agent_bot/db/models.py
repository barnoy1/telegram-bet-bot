"""Data models for the betting bot."""

from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from typing import Optional
from enum import Enum
from sqlalchemy import Column, BigInteger, String, DateTime, Numeric, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class EventState(str, Enum):
    """States for an event (group)."""
    IDLE = "IDLE"
    BETTING_ACTIVE = "BETTING_ACTIVE"
    CLOSED = "CLOSED"


class ParticipantState(str, Enum):
    """States for a participant."""
    NOT_JOINED = "NOT_JOINED"
    IN_GAME = "IN_GAME"
    OUT = "OUT"


# Export enum values for cleaner code
NOT_JOINED, IN_GAME, OUT = ParticipantState


# SQLAlchemy ORM Models
class UserModel(Base):
    """SQLAlchemy model for users table."""
    __tablename__ = 'users'

    user_id = Column(BigInteger, primary_key=True)
    username = Column(String, nullable=False)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EventModel(Base):
    """SQLAlchemy model for events table."""
    __tablename__ = 'events'

    event_id = Column(BigInteger, primary_key=True)
    group_name = Column(String, nullable=False)
    creator_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    state = Column(SQLEnum(EventState), default=EventState.IDLE)
    created_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    last_activity_timestamp = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    creator = relationship("UserModel")


class ParticipantModel(Base):
    """SQLAlchemy model for participants table."""
    __tablename__ = 'participants'

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(BigInteger, ForeignKey('events.event_id'), nullable=False)
    user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    state = Column(SQLEnum(ParticipantState), default=NOT_JOINED)
    total_bet_amount = Column(Numeric(10, 2), default=0)
    current_bet_amount = Column(Numeric(10, 2), default=0)
    prize_amount = Column(Numeric(10, 2), default=0)
    rebuy_count = Column(Integer, default=0)
    joined_at = Column(DateTime, default=datetime.utcnow)
    settled_at = Column(DateTime, nullable=True)

    event = relationship("EventModel")
    user = relationship("UserModel")


class TransactionModel(Base):
    """SQLAlchemy model for transactions table."""
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(BigInteger, ForeignKey('events.event_id'), nullable=False)
    from_user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    to_user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    event = relationship("EventModel")
    from_user = relationship("UserModel", foreign_keys=[from_user_id])
    to_user = relationship("UserModel", foreign_keys=[to_user_id])


class LanguageModel(Base):
    """SQLAlchemy model for language tracking per group."""
    __tablename__ = 'languages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(BigInteger, nullable=False)
    language_code = Column(String(10), nullable=False)
    count = Column(Integer, default=1)

    __table_args__ = (
        {'sqlite_autoincrement': True}
    )


# Dataclasses for backward compatibility
@dataclass
class User:
    """Represents a Telegram user."""
    user_id: int
    username: str
    first_seen: str
    last_seen: str


@dataclass
class Event:
    """Represents a betting event (group)."""
    event_id: int
    group_name: str
    creator_id: int
    state: EventState
    created_at: str
    closed_at: Optional[str] = None
    last_activity_timestamp: Optional[str] = None


@dataclass
class Participant:
    """Represents a participant in an event."""
    id: int
    event_id: int
    user_id: int
    username: str
    state: ParticipantState
    total_bet_amount: Decimal
    current_bet_amount: Decimal
    prize_amount: Decimal
    rebuy_count: int
    joined_at: str
    settled_at: Optional[str] = None


@dataclass
class Transaction:
    """Represents a settlement transaction."""
    id: int
    event_id: int
    from_user_id: int
    to_user_id: int
    amount: Decimal
    created_at: str
