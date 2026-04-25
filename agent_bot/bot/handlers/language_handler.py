"""Language selection handler."""

import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


class LanguageHandler:
    """Handles language selection callbacks."""

    def __init__(self, storage=None):
        self.storage = storage

    async def handle_language_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle language selection callback from inline keyboard."""
        query = update.callback_query
        if not query:
            return
        
        await query.answer()
        
        # Parse callback data: lang_en_{group_id}
        callback_data = query.data
        if not callback_data.startswith("lang_"):
            return
        
        parts = callback_data.split("_")
        if len(parts) < 3:
            return
        
        lang_code = parts[1]
        group_id = int(parts[2])
        
        # Store language preference for group
        try:
            if self.storage:
                self.storage.set_group_language(group_id, lang_code)
            
            lang_names = {
                'en': 'English',
                'he': 'עברית',
                'ru': 'Русский'
            }
            
            confirmation = f"✅ Language set to {lang_names.get(lang_code, lang_code)}"
            await query.edit_message_text(confirmation)
            logger.info(f"Group {group_id} language set to {lang_code}")
        except Exception as e:
            logger.error(f"Failed to set language for group {group_id}: {e}")
            await query.edit_message_text("❌ Failed to set language")
