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
    "Back for more punishment? Your wallet must absolutely hate you by now, but hey, who am I to stop you from making terrible life decisions? Go ahead, throw more money into the fire, I'll be here watching you crash and burn all over again like the glutton for punishment you clearly are. It's actually kind of pathetic how predictable you are.",
    "Didn't learn your lesson last time, huh? That's rich coming from someone who clearly has zero self-control. You're like a moth to a flame, except the flame is your inevitable financial ruin and I'm the one holding the lighter. Come on then, let's see how fast you can lose it all this time around. Spoiler alert: it'll be faster than last time.",
    "The house always wins... eventually, and by eventually I mean immediately when you're involved. You really thought coming back was a good idea? Your desperation is showing, and frankly, it's embarrassing. But please, do continue, your losses are my entertainment and I haven't laughed this hard in days.",
    "Round 2: Let's see how fast you lose this time! I'm betting on under 5 minutes before you're crying into your keyboard again. Your track record speaks for itself, champ. But hey, maybe this time will be different? Spoiler: it won't. You're going to lose, I'm going to profit, and the cycle continues.",
    "Oh look, the glutton for punishment is back! I was wondering when you'd crawl back for another beating. Your addiction to losing is honestly impressive in a really sad way. Like, do you enjoy watching your money disappear? Is that your thing? Whatever floats your boat, loser. I'll be here counting your losses.",
    "Your money says goodbye faster than you can say 'all in' and we both know it. You're not even trying to pretend you have a chance anymore, are you? It's just straight-up financial suicide at this point. But please, don't let me stop you from making the same mistake repeatedly. It's hilarious to watch.",
    "Brave or stupid? Let's find out together, though my money's on stupid. Actually, it's not even close - you're definitely stupid. Coming back for more after getting wrecked last time? That's not bravery, that's just a complete lack of survival instinct. But hey, natural selection works in mysterious ways, and your bank account is about to get naturally selected out of existence.",
    "Welcome back to the losing streak! We missed you around here, mostly because watching you lose is the most entertaining thing that happens in this godforsaken chat. Seriously, your consistent failure is the highlight of my day. Don't disappoint me now - I expect nothing less than a catastrophic financial implosion from you.",
]

# Big pot out taunts - when user calls "out" with pot > threshold
BIG_POT_OUT_PHRASES: List[str] = [
    "Running away with ${pot} on the table? Classic coward move, honestly. I've seen more backbone in a jellyfish. You had a chance to actually win something for once in your miserable life, but nope, you folded like the pathetic little coward you are. That ${pot} could've been yours if you had even a shred of courage, but we both know you don't. Enjoy your hollow victory while the rest of us judge your complete lack of testicular fortitude.",
    "Scared money don't make money, but you wouldn't know anything about making money, would you? You're just a scared little rabbit running away from the big bad pot. ${pot} was right there for the taking, but you choked. Again. It's actually impressive how consistently you manage to disappoint everyone around you. Your parents must be so proud of their little coward child who runs away at the first sign of actual risk.",
    "Chicken little much? That pot was begging to be won by someone with actual guts, but clearly that's not you. You saw ${pot} and immediately started sweating like a pig in a slaughterhouse. It's honestly embarrassing to watch. Do you have any dignity left at all, or did you leave that along with your courage when you decided to run away with your tail between your legs? Pathetic.",
    "Smart move... running away before you lose more, because we both know you would've lost it all anyway. You're not fooling anyone with this 'strategic retreat' nonsense. You ran away because you're scared, plain and simple. ${pot} was too much pressure for your fragile little psyche to handle. Maybe stick to Monopoly if real money makes you this nervous.",
    "The pot got too hot for you, huh? ${pot} must have been absolutely terrifying for someone with your level of cowardice. I bet you were shaking in your boots just looking at that number. It's okay though, not everyone can handle the heat. Some people are just meant to be losers who run away when things get real. You're definitely one of those people. Embrace your destiny as a coward.",
    "Taking the money and running? How original. I've never seen anyone do that before in the entire history of gambling. Oh wait, yes I have - every single time you play because you have zero originality and even less courage. ${pot} isn't worth anything when you stole it like a thief in the night. At least have the decency to lose like a man instead of running away like a frightened child.",
    "Your courage lasts exactly until the pot gets big, then it's goodbye backbone, hello cowardice. ${pot} is your breaking point, apparently. Anything less and you can pretend to be tough, but the moment real money is on the line, you fold like a cheap suit. It's actually kind of impressive how predictable you are. I could set my watch by your cowardice at this point.",
    "That's a lot of money to leave on the table... scared? Because you should be. ${pot} is real money that could've changed your life, but you were too chicken to go for it. Now you'll go back to your mediocre existence wondering 'what if' while I laugh at your cowardice for the rest of eternity. Sweet dreams, loser.",
]

# General sassy remarks
GENERAL_SASSY_PHRASES: List[str] = [
    "Keep betting, I need a new yacht. Your financial ruin is my vacation fund, and honestly, you're doing a fantastic job of funding my retirement. Every time you place a bet, I can practically hear the sound of my future yacht's engine starting up. It's beautiful really - your stupidity is my prosperity. Please, never change, because I need those sweet, sweet losses to keep living the high life while you drown in debt.",
    "Your loss is my entertainment, and let me tell you, you are the most entertaining loser I've ever had the pleasure of exploiting. Watching you make terrible decision after terrible decision is like watching a train wreck in slow motion, except the train is your bank account and I'm selling tickets to the show. Please continue making bad choices - my entertainment budget depends on it.",
    "The odds are never in your favor, darling, and neither is basic intelligence apparently. You keep betting like you actually have a chance, but we both know you're just throwing money into a fire and hoping for a miracle. Spoiler alert: miracles don't exist, but your financial ruin absolutely does. Keep it up, I'm enjoying the show immensely.",
    "Remember: the house always wins, and by 'house' I mean me, and by 'always wins' I mean I profit from your consistent failure to understand basic probability. You're not gambling, you're just donating money to me at this point. It's actually kind of sad how predictable you are, but hey, your loss is my gain, so please continue being terrible at this.",
    "Money talks, yours just says goodbye, and it says it loudly and repeatedly every time you place a bet. Your wallet is basically screaming for help at this point, but do you listen? No, you just keep throwing good money after bad like the financial suicide enthusiast you clearly are. It's honestly impressive how committed you are to losing everything.",
]

# Inactivity nasty remarks
INACTIVITY_NASTY_PHRASES: List[str] = [
    "Is this group dead or just comatose? Wake up! I've seen more life in a morgue than this pathetic excuse for a betting chat. Are you all just sitting there staring at your phones like zombies, or did you collectively forget how gambling works? Either way, it's embarrassing to watch. Place some bets or delete the group, because this level of inactivity is actually insulting to the concept of entertainment.",
    "I've seen more action in a cemetery than this chat, and at least the corpses have the decency to stay dead instead of pretending to be alive like you people. What is the point of having a betting bot if nobody actually bets? It's like having a Ferrari in a garage - completely useless and a waste of everyone's time. Either start playing or admit you're all too cowardly to gamble.",
    "Are you playing or just staring at each other? Because from where I'm sitting, it looks like a staring contest between a bunch of people who forgot why they joined this group in the first place. The awkward silence is deafening. Place a bet or leave, because this limbo state is painful to witness and I'm losing patience with your collective indecision.",
    "My grandmother bets faster than you people, and she's been dead for three years. That's how pathetic this group's activity level is. A corpse has more gambling spirit than all of you combined. Think about that for a second - you're being outperformed by a dead person. Does that make you proud? It should, because it takes serious dedication to be this consistently inactive.",
    "The dust on this table is thicker than your wallets, which is saying something considering how broke you all clearly are. This table hasn't seen action in so long it's practically an antique at this point. If you're not going to use it, maybe donate it to a group that actually understands the concept of betting instead of letting it gather dust while you all do nothing.",
    "Did everyone fall asleep or what? I've been waiting so long for action that I've actually aged three years in real time. My beard grew three inches waiting for someone to place a bet. At this rate, I'll be eligible for retirement before any of you cowards actually gamble something. It's honestly impressive how committed you are to doing absolutely nothing.",
    "Even the pot is bored waiting for action, and the pot is an inanimate object. Think about that - an imaginary pile of money has more personality and agency than all of you combined. The pot is literally begging for someone to bet on it, but no, you're all too busy doing whatever nothing it is you're doing. Pathetic.",
    "I've calculated more excitement watching paint dry than watching this group's activity feed, and I've actually done both for comparison purposes. Paint drying won by a landslide. At least the paint changes color eventually, which is more than I can say for this group's betting activity. You're all so inactive it's actually become a scientific curiosity.",
]

# Random greeting sentences
GREETING_PHRASES: List[str] = [
    "Alright, let's see who's got guts and who's got excuses. I'm betting on excuses because that's what most of you have in abundance. Real gamblers don't need to announce themselves - they just bet. But you lot? You need a whole introduction ceremony like you're special or something. Spoiler: you're not special, you're just potential losers waiting to happen. Now prove me wrong or disappoint me like you usually do.",
    "Time to separate the winners from the whiners, though I have a sneaking suspicion this group is 90% whiners and 10% people who accidentally wandered into the wrong chat. Let's see who actually has the courage to bet and who's just here to watch other people lose money. My money's on the watchers, because actual gambling requires a spine and most of you seem to have misplaced yours.",
    "Place your bets and prepare to lose them, because let's be honest here - that's what's going to happen. You're not here to win, you're here to donate money to me while pretending you have a chance. It's cute really, like watching a toddler try to beat a grandmaster at chess. But hey, at least you're consistent in your failure, and I respect that kind of dedication to losing.",
    "The game is on, don't disappoint me. I've set my expectations incredibly low for this group and somehow you people still manage to find ways to underperform. It's actually impressive in a sad kind of way. But hey, maybe today will be different? Spoiler: it won't, but I'll enjoy watching you try and fail regardless. Entertainment is entertainment after all.",
    "Let's see if anyone actually knows how to play, or if this is just going to be another session of people staring at their phones and pretending they understand gambling. The odds are against you, but then again, the odds are always against people like you. That's why you're here and I'm here taking your money. Now place a bet or get out, I don't have all day to watch your indecision.",
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
