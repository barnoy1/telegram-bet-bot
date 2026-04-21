"""Inactivity monitoring service for sending random greetings and nasty remarks."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from telegram import Bot
from bot.personality.greetings import GreetingLibrary
from bot.personality.bookie_personality import BookiePersonality
from config import (
    INACTIVITY_ENABLED,
    INACTIVITY_TIMEOUT_MINUTES,
    INACTIVITY_RANDOM_MESSAGE_INTERVAL_MINUTES,
    INACTIVITY_MAX_RANDOM_MESSAGES,
)

logger = logging.getLogger(__name__)


class InactivityMonitor:
    """Service for monitoring group inactivity and sending timed messages."""

    def __init__(self, bot: Bot, personality: BookiePersonality, storage):
        """Initialize the inactivity monitor.
        
        Args:
            bot: Telegram Bot instance
            personality: BookiePersonality instance for sassy remarks
            storage: Storage instance for tracking activity
        """
        self.bot = bot
        self.personality = personality
        self.storage = storage
        self.enabled = INACTIVITY_ENABLED
        self.timeout_minutes = INACTIVITY_TIMEOUT_MINUTES
        self.interval_minutes = INACTIVITY_RANDOM_MESSAGE_INTERVAL_MINUTES
        self.max_messages = INACTIVITY_MAX_RANDOM_MESSAGES
        
        # Track inactivity state per group
        self.group_state: Dict[int, Dict] = {}
        self._monitor_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self):
        """Start the inactivity monitoring background task."""
        if not self.enabled:
            logger.info("Inactivity monitoring is disabled")
            return
        
        if self._running:
            logger.warning("Inactivity monitor is already running")
            return
        
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Inactivity monitor started")

    async def stop(self):
        """Stop the inactivity monitoring background task."""
        if not self._running:
            return
        
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Inactivity monitor stopped")

    async def update_activity(self, group_id: int):
        """Update activity timestamp for a group.
        
        Args:
            group_id: Telegram group ID
        """
        if not self.enabled:
            return
        
        # Update in database
        self.storage.update_group_activity(group_id, datetime.utcnow())
        
        # Reset inactivity state if group was being monitored
        if group_id in self.group_state:
            logger.info(f"Activity detected in group {group_id}, resetting inactivity state")
            del self.group_state[group_id]

    async def send_greeting(self, group_id: int):
        """Send a random greeting message to a group.
        
        Args:
            group_id: Telegram group ID
        """
        greeting = GreetingLibrary.get_random_greeting()
        try:
            await self.bot.send_message(chat_id=group_id, text=f"💬 {greeting}", parse_mode="Markdown")
            logger.info(f"Sent greeting to group {group_id}")
        except Exception as e:
            logger.error(f"Failed to send greeting to group {group_id}: {e}")

    async def send_nasty_remark(self, group_id: int):
        """Send a nasty remark to an inactive group.
        
        Args:
            group_id: Telegram group ID
        """
        remark = self.personality.get_inactivity_nasty()
        if remark:
            try:
                await self.bot.send_message(chat_id=group_id, text=f"💬 {remark}", parse_mode="Markdown")
                logger.info(f"Sent nasty remark to group {group_id}")
            except Exception as e:
                logger.error(f"Failed to send nasty remark to group {group_id}: {e}")

    async def _monitor_loop(self):
        """Background task to monitor group inactivity."""
        while self._running:
            try:
                await self._check_inactivity()
                # Check every minute
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in inactivity monitor loop: {e}", exc_info=True)
                await asyncio.sleep(60)

    async def _check_inactivity(self):
        """Check all groups for inactivity and send appropriate messages."""
        if not self.enabled:
            return
        
        groups = self.storage.get_all_groups()
        now = datetime.utcnow()
        
        for group in groups:
            group_id = group.group_id
            last_activity = group.last_activity_timestamp
            
            if last_activity is None:
                # Initialize activity timestamp if not set
                self.storage.update_group_activity(group_id, now)
                continue
            
            # Parse timestamp if it's a string
            if isinstance(last_activity, str):
                from datetime import datetime as dt
                last_activity = dt.fromisoformat(last_activity)
            
            inactive_duration = (now - last_activity).total_seconds() / 60  # in minutes
            
            # Initialize group state if not exists
            if group_id not in self.group_state:
                self.group_state[group_id] = {
                    "messages_sent": 0,
                    "last_check": now
                }
            
            state = self.group_state[group_id]
            
            # Check if we should send a random message
            if state["messages_sent"] < self.max_messages:
                time_since_last_check = (now - state["last_check"]).total_seconds() / 60
                if time_since_last_check >= self.interval_minutes:
                    await self.send_greeting(group_id)
                    state["messages_sent"] += 1
                    state["last_check"] = now
            # Check if we should send nasty remark
            elif inactive_duration >= self.timeout_minutes:
                await self.send_nasty_remark(group_id)
                # Remove from monitoring after sending nasty remark
                del self.group_state[group_id]
