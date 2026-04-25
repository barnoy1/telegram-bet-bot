"""Message formatter for bot responses."""

from agent_bot.bot.personality.bookie_personality import BookiePersonality
from agent_bot.bot.services.language_service import LanguageService


class MessageFormatter:
    """Formats bot messages for consistent presentation."""

    def __init__(self, personality: BookiePersonality = None, language_service: LanguageService = None, group_id: int = None):
        # Use the personality passed in from main.py - it has language_service
        # Only create a new one if none was passed (fallback)
        self.personality = personality
        self.language_service = language_service
        self.group_id = group_id

    def format_start_message(self) -> str:
        """Format the start/welcome message."""
        sassy_comment = self.personality.get_general_sassy(self.group_id)
        sassy_line = f"\n💬 {sassy_comment}" if sassy_comment else ""

        if self.language_service and self.group_id:
            header = self.language_service.get_translation(self.group_id, 'start.header')
            initialized = self.language_service.get_translation(self.group_id, 'start.initialized')
            description = self.language_service.get_translation(self.group_id, 'start.description')
            quick_start = self.language_service.get_translation(self.group_id, 'start.quick_start')
            quick_start_text = self.language_service.get_translation(self.group_id, 'start.quick_start_text')
            help_command = self.language_service.get_translation(self.group_id, 'start.help_command')
        else:
            # Fallback to English
            header = "POKER BOT"
            initialized = "Bot Initialized"
            description = "I'm ready to track your poker bets and calculate fair settlements."
            quick_start = "Quick Start:"
            quick_start_text = "Just send a number to place a bet"
            help_command = "Type `/h` for all commands"

        message = (
            "\u200E"  # LTR marker to prevent Hebrew reversal
            "━━━━━━━━━━━━━\n"
            f"🃏 *{header}* 🃏\n"
            "━━━━━━━━━━━━━\n\n"
            f"✅ *{initialized}*\n\n"
            f"{description}\n\n"
            f"💡 *{quick_start}* {quick_start_text}\n"
            f"📝 {help_command}\n"
            f"{sassy_line}\n"
            "━━━━━━━━━━━━━"
        )

        # Note: RTL formatting disabled - Telegram handles RTL automatically based on text segments
        # Applying RTL formatting to entire message causes English text to be reversed

        return message

    def format_help_message(self) -> str:
        """Format the help message."""
        sassy_comment = self.personality.get_general_sassy(self.group_id)
        sassy_line = f"\n💬 {sassy_comment}" if sassy_comment else ""

        if self.language_service and self.group_id:
            header = self.language_service.get_translation(self.group_id, 'help.header')
            poker_commands = self.language_service.get_translation(self.group_id, 'help.poker_commands')
            str_desc = self.language_service.get_translation(self.group_id, 'help.str_desc')
            out_desc = self.language_service.get_translation(self.group_id, 'help.out_desc')
            quick_bet = self.language_service.get_translation(self.group_id, 'help.quick_bet')
            quick_bet_text = self.language_service.get_translation(self.group_id, 'help.quick_bet_text')
            info_commands = self.language_service.get_translation(self.group_id, 'help.info_commands')
            sts_desc = self.language_service.get_translation(self.group_id, 'help.sts_desc')
            l_desc = self.language_service.get_translation(self.group_id, 'help.l_desc')
            t_desc = self.language_service.get_translation(self.group_id, 'help.t_desc')
            v_desc = self.language_service.get_translation(self.group_id, 'help.v_desc')
            mgmt_commands = self.language_service.get_translation(self.group_id, 'help.mgmt_commands')
            u_desc = self.language_service.get_translation(self.group_id, 'help.u_desc')
            r_desc = self.language_service.get_translation(self.group_id, 'help.r_desc')
            h_desc = self.language_service.get_translation(self.group_id, 'help.h_desc')
        else:
            # Fallback to English
            header = "COMMANDS"
            poker_commands = "Poker Commands:"
            str_desc = "Initialize bot in this group"
            out_desc = "Leave with specified amount"
            quick_bet = "Quick Bet:"
            quick_bet_text = "Just send a number (e.g., `50`)"
            info_commands = "Information Commands:"
            sts_desc = "Show current table status"
            l_desc = "Change bot language"
            t_desc = "Show settlement transactions"
            v_desc = "Show bot version"
            mgmt_commands = "Management Commands:"
            u_desc = "Undo last bet"
            r_desc = "Reset all bets"
            h_desc = "Show this help"

        message = (
            "\u200E"  # LTR marker to prevent Hebrew reversal
            "━━━━━━━━━━━━━\n"
            f"📚 *{header}* 📚\n"
            "━━━━━━━━━━━━━\n\n"
            f"🃏 *{poker_commands}*\n"
            f"  `str` — {str_desc}\n"
            f"  `out <amount>` — {out_desc}\n\n"
            f"  *{quick_bet}* {quick_bet_text}\n\n"
            f"📊 *{info_commands}*\n"
            f"  `s` — {sts_desc}\n"
            f"  `l` — {l_desc}\n"
            f"  `t` — {t_desc}\n"
            f"  `v` — {v_desc}\n\n"
            f"🔧 *{mgmt_commands}*\n"
            f"  `u` — {u_desc}\n"
            f"  `r` — {r_desc}\n"
            f"  `h` — {h_desc}\n\n"
            f"{sassy_line}\n"
            "━━━━━━━━━━━━━"
        )

        # Note: RTL formatting disabled - Telegram handles RTL automatically based on text segments
        # Applying RTL formatting to entire message causes English text to be reversed

        return message

    def format_welcome_message(self) -> str:
        """Format the welcome message when bot joins a group."""
        if self.language_service and self.group_id:
            header = self.language_service.get_translation(self.group_id, 'welcome.header')
            joined = self.language_service.get_translation(self.group_id, 'welcome.joined')
            description = self.language_service.get_translation(self.group_id, 'welcome.description')
            to_get_started = self.language_service.get_translation(self.group_id, 'welcome.to_get_started')
            str_instruction = self.language_service.get_translation(self.group_id, 'welcome.str_instruction')
            need_help = self.language_service.get_translation(self.group_id, 'welcome.need_help')
            help_instruction = self.language_service.get_translation(self.group_id, 'welcome.help_instruction')
        else:
            # Fallback to English
            header = "WELCOME"
            joined = "Poker Bot has joined the group!"
            description = "I'll help you track poker bets and calculate fair settlements automatically."
            to_get_started = "To get started:"
            str_instruction = "Type `/str` to initialize the bot"
            need_help = "Need help?"
            help_instruction = "Type `/h` anytime"

        message = (
            "\u200E"  # LTR marker to prevent Hebrew reversal
            "━━━━━━━━━━━━━\n"
            f"👋 *{header}* 👋\n"
            "━━━━━━━━━━━━━\n\n"
            f"✨ *{joined}*\n\n"
            f"{description}\n\n"
            f"🚀 *{to_get_started}*:\n"
            f"  {str_instruction}\n\n"
            f"📖 *{need_help}?* {help_instruction}\n"
            "━━━━━━━━━━━━━"
        )

        # Note: RTL formatting disabled - Telegram handles RTL automatically based on text segments
        # Applying RTL formatting to entire message causes English text to be reversed

        return message
