"""Language repository for database operations."""

from typing import Dict
from sqlalchemy import delete
from sqlalchemy.orm import Session

from agent_bot.db.models import LanguageModel
from agent_bot.db.repositories.base_repository import BaseRepository


class LanguageRepository(BaseRepository):
    """Repository for language-related database operations."""

    def increment_language(self, group_id: int, language_code: str) -> bool:
        """Increment language count for a group."""
        lang_record = self.session.query(LanguageModel).filter(
            LanguageModel.group_id == group_id,
            LanguageModel.language_code == language_code
        ).first()

        if lang_record:
            lang_record.count += 1
        else:
            lang_record = LanguageModel(
                group_id=group_id,
                language_code=language_code,
                count=1
            )
            self.session.add(lang_record)

        self.commit()
        return True

    def get_language_stats(self, group_id: int) -> Dict[str, int]:
        """Get language statistics for a group."""
        results = self.session.query(LanguageModel).filter(
            LanguageModel.group_id == group_id
        ).all()
        return {r.language_code: r.count for r in results}

    def set_group_language(self, group_id: int, language_code: str) -> bool:
        """Set the group's language preference directly (clears existing stats)."""
        # Delete all existing language records for this group
        self.session.execute(
            delete(LanguageModel).where(LanguageModel.group_id == group_id)
        )
        
        # Create a new record with high count to ensure it's dominant
        lang_record = LanguageModel(
            group_id=group_id,
            language_code=language_code,
            count=1000
        )
        self.session.add(lang_record)
        self.commit()
        return True
