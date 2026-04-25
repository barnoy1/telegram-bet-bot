"""User repository for database operations."""

from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session

from agent_bot.db.models import User, UserModel
from agent_bot.db.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository):
    """Repository for user-related database operations."""

    def get_or_create_user(self, user_id: int, username: str = None) -> User:
        """Get existing user or create new one."""
        user = self.session.query(UserModel).filter(
            UserModel.user_id == user_id
        ).first()
        
        if user:
            # Update username if provided
            if username and user.username != username:
                user.username = username
                self.commit()
                self.session.refresh(user)
            return self._model_to_dataclass(user, User)
        
        # Create new user
        new_user = UserModel(
            user_id=user_id,
            username=username or f"user_{user_id}"
        )
        self.session.add(new_user)
        self.commit()
        self.session.refresh(new_user)
        return self._model_to_dataclass(new_user, User)

    def update_last_seen(self, user_id: int) -> bool:
        """Update user's last seen timestamp."""
        user = self.session.query(UserModel).filter(
            UserModel.user_id == user_id
        ).first()
        if user:
            user.last_seen = datetime.utcnow()
            self.commit()
            return True
        return False

    def get_user(self, user_id: int) -> Optional[User]:
        """Get a user by ID."""
        user = self.session.query(UserModel).filter(
            UserModel.user_id == user_id
        ).first()
        return self._model_to_dataclass(user, User)

    def get_all_users(self) -> List[User]:
        """Get all users."""
        users = self.session.query(UserModel).all()
        return [self._model_to_dataclass(u, User) for u in users]
