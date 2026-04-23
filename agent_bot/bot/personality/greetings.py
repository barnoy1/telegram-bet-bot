"""Greeting phrases for bot inactivity monitoring using Sleazy persona."""

from typing import List, Optional
import random


# Random greeting sentences - Sleazy persona
GREETING_PHRASES: List[str] = [
    "New blood! Pull up a crate, kid. Try not to get any tears on the felt, I just had it vacuumed.",
    "Whoa! Look at this philanthropist! Sit down, Big Shot—make yourself comfortable. I'll make sure the guys treat your chips with 'respect' before they take 'em.",
    "Fresh meat at the table! Welcome to the slaughterhouse, champ. Don't say I didn't warn you.",
    "Another sucker walks through the door. Pull up a chair and prepare to lose your shirt. It's what we do here.",
    "Alright, let's see who's got guts and who's got excuses. I'm betting on excuses because that's what most of you have in abundance.",
    "Time to separate the winners from the whiners, though I have a sneaking suspicion this group is 90% whiners and 10% people who accidentally wandered into the wrong chat.",
    "Place your bets and prepare to lose them, because let's be honest here - that's what's going to happen. You're not here to win, you're here to donate money to me.",
    "The game is on, don't disappoint me. I've set my expectations incredibly low for this group and somehow you people still manage to find ways to underperform.",
]


class GreetingLibrary:
    """Library of greeting phrases for inactivity monitoring."""

    def __init__(self, language_service=None):
        """Initialize the greeting library.
        
        Args:
            language_service: Language service for translated greetings
        """
        self.language_service = language_service

    def get_random_greeting(self, group_id: int = None) -> str:
        """Get a random greeting phrase.
        
        Args:
            group_id: Group ID for language detection
        
        Returns:
            A random greeting phrase (translated if language service is available)
        """
        # Try to get translated greeting if language service is available
        if self.language_service and group_id:
            try:
                # Use fresh_meat.greeting from Hebrew translations
                greeting = self.language_service.get_translation(group_id, 'fresh_meat.greeting')
                # The translation returns a list, so we need to pick a random one
                if isinstance(greeting, list):
                    greeting = random.choice(greeting)
                return greeting
            except Exception:
                # Fallback to English if translation fails
                pass
        
        return random.choice(GREETING_PHRASES)
