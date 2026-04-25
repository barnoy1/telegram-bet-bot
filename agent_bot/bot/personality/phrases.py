"""Phrase library for sassy bookie personality."""

from enum import Enum
from typing import List
import random


class PhraseCategory(Enum):
    """Categories of sassy phrases."""
    REBUY = "rebuy"
    BIG_POT_OUT = "big_pot_out"
    GENERAL_SASSY = "general_sassy"
    INACTIVITY_NASTY = "inactivity_nasty"
    GREETING = "greeting"
    NEW_PLAYER = "new_player"
    BET_PLACED = "bet_placed"
    BIG_BET = "big_bet"
    HESITATION = "hesitation"
    WINNER_LEAVING = "winner_leaving"
    LOSER_LEAVING = "loser_leaving"


# Rebuy taunts - when a user who previously "out" places a new bet
REBUY_PHRASES: List[str] = [
    "Back for more punishment?",
    "Didn't learn your lesson last time?",
    "The house always wins... eventually.",
    "Round 2: Let's see how fast you lose.",
    "Glutton for punishment, huh?",
    "Your money says goodbye again.",
    "Brave or stupid? I'm betting on stupid.",
    "Welcome back to the losing streak!",
]

# Big pot out taunts - when user calls "out" with pot > threshold
BIG_POT_OUT_PHRASES: List[str] = [
    "Running away with ${pot}? Classic coward move.",
    "Scared money don't make money.",
    "Chicken little much? That pot was begging to be won.",
    "Smart move... running away before you lose more.",
    "The pot got too hot for you, huh?",
    "Taking the money and running? How original.",
    "Your courage lasts until the pot gets big.",
    "That's a lot of money to leave on the table... scared?",
]

# General sassy remarks
GENERAL_SASSY_PHRASES: List[str] = [
    "Keep betting, I need a new yacht.",
    "Your loss is my entertainment.",
    "The odds are never in your favor.",
    "House always wins, darling.",
    "Money talks, yours just says goodbye.",
]

# Inactivity nasty remarks
INACTIVITY_NASTY_PHRASES: List[str] = [
    "Is this group dead or just comatose?",
    "I've seen more action in a cemetery.",
    "Are you playing or just staring?",
    "My grandmother bets faster than you people.",
    "The dust on this table is thicker than your wallets.",
    "Did everyone fall asleep or what?",
    "Even the pot is bored waiting for action.",
    "I've seen more excitement watching paint dry.",
]

# Random greeting sentences
GREETING_PHRASES: List[str] = [
    "Let's see who's got guts and who's got excuses.",
    "Time to separate the winners from the whiners.",
    "Place your bets and prepare to lose them.",
    "The game is on, don't disappoint me.",
    "Let's see if anyone actually knows how to play.",
]

# New player greetings - Sleazy persona
NEW_PLAYER_PHRASES: List[str] = [
    "New blood! Pull up a crate, kid. Try not to get any tears on the felt, I just had it vacuumed.",
    "Whoa! Look at this philanthropist! Sit down, Big Shot—make yourself comfortable. I'll make sure the guys treat your chips with 'respect' before they take 'em.",
    "Fresh meat at the table! Welcome to the slaughterhouse, champ. Don't say I didn't warn you.",
    "Another sucker walks through the door. Pull up a chair and prepare to lose your shirt. It's what we do here.",
]

# Bet placement reactions - Sleazy persona
BET_PLACED_PHRASES: List[str] = [
    "Oh, he's feeling spicy! Pushing some plastic into the middle. You trying to buy a clue or just showing off?",
    "There it is! The 'Hero Move.' You betting like you've got a printer in the basement, Champ. You sure your heart can take that much stress?",
    "Action! Finally. I was starting to think this was a library. Keep the gravy flowing.",
]

# Big bet reactions - Sleazy persona
BIG_BET_PHRASES: List[str] = [
    "Whoa, whoa! Look at 'Big Money' over here! [Taps the table] That's a bold bet for a guy wearing a knock-off watch. You chasing a dream, Rookie, or did you just get tired of having a full wallet? Either way, the pot's looking healthy—and I love a healthy table.",
    "That's a lot of plastic you just threw in the middle. You feeling lucky or just stupid? Either way, the house appreciates the donation.",
    "Now we're talking! That's what I call putting your money where your mouth is. Or maybe you're just compensating for something. Who knows, who cares—it's all the same to me.",
]

# Hesitation taunts - Sleazy persona
HESITATION_PHRASES: List[str] = [
    "Tick-tock, Einstein. The ice in my drink is melting faster than your resolve. You in or you folding your pride again?",
    "What is this, a knitting circle? Make a move before I start charging rent by the minute.",
    "I've got all day. Well, actually I don't, but watching you sweat is entertaining enough that I might make an exception.",
]

# Winner leaving taunts - Sleazy persona
WINNER_LEAVING_PHRASES: List[str] = [
    "Leaving already? The sun isn't even up! Taking the family's money and running? Real classy, Einstein. Real classy.",
    "Taking the gravy and running? Typical. Don't spend it all in one place, champ. Or do, I don't care—it'll be back here soon enough.",
]

# Loser leaving taunts - Sleazy persona
LOSER_LEAVING_PHRASES: List[str] = [
    "Tapped out, huh? Don't look at me—I'm just the guy with the rake. Don't worry, we'll name a chair after your contribution tonight.",
    "The door's that way. Thanks for playing, thanks for paying. Come back when your wallet recovers. Or don't—either way, the house wins.",
]


class PhraseLibrary:
    """Library of sassy phrases organized by category."""

    @staticmethod
    def get_phrase(category: PhraseCategory, context: dict = None) -> str:
        """Get a random phrase from a category.
        
        Args:
            category: The category of phrase to retrieve
            context: Optional context dict for phrase interpolation (e.g., {"pot": 1000})
            
        Returns:
            A random phrase from the category
        """
        phrases = []
        
        if category == PhraseCategory.REBUY:
            phrases = REBUY_PHRASES
        elif category == PhraseCategory.BIG_POT_OUT:
            phrases = BIG_POT_OUT_PHRASES
        elif category == PhraseCategory.GENERAL_SASSY:
            phrases = GENERAL_SASSY_PHRASES
        elif category == PhraseCategory.INACTIVITY_NASTY:
            phrases = INACTIVITY_NASTY_PHRASES
        elif category == PhraseCategory.GREETING:
            phrases = GREETING_PHRASES
        elif category == PhraseCategory.NEW_PLAYER:
            phrases = NEW_PLAYER_PHRASES
        elif category == PhraseCategory.BET_PLACED:
            phrases = BET_PLACED_PHRASES
        elif category == PhraseCategory.BIG_BET:
            phrases = BIG_BET_PHRASES
        elif category == PhraseCategory.HESITATION:
            phrases = HESITATION_PHRASES
        elif category == PhraseCategory.WINNER_LEAVING:
            phrases = WINNER_LEAVING_PHRASES
        elif category == PhraseCategory.LOSER_LEAVING:
            phrases = LOSER_LEAVING_PHRASES
        else:
            phrases = GENERAL_SASSY_PHRASES
        
        phrase = random.choice(phrases)
        
        # Interpolate context variables if provided
        if context:
            for key, value in context.items():
                phrase = phrase.replace(f"${{{key}}}", str(value))
        
        return phrase
