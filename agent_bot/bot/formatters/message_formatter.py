"""Message formatter for bot responses."""

from agent_bot.bot.personality.llm_persona_service import LLMPersonalityService


class MessageFormatter:
    """Formats bot messages for consistent presentation (English only)."""

    def __init__(self, personality: LLMPersonalityService = None):
        self.personality = personality

    def format_start_message(self) -> str:
        """Format the start/welcome message."""
        header = "POKER BOT"
        initialized = "Bot Initialized"
        description = "I'm ready to track your poker bets and calculate fair settlements."
        quick_start = "Quick Start:"
        quick_start_text = "Just send a number to place a bet"
        help_command = "Type `h` for all commands"

        message = (
            "━━━━━━━━━━━━━\n"
            f"🃏 *{header}* 🃏\n"
            "━━━━━━━━━━━━━\n\n"
            f"✅ *{initialized}*\n\n"
            f"{description}\n\n"
            f"💡 *{quick_start}* {quick_start_text}\n"
            f"📝 {help_command}\n"
            "━━━━━━━━━━━━━"
        )

        return message

    def format_help_message(self) -> str:
        """Format the help message."""
        header = "COMMANDS"
        poker_commands = "Poker Commands:"
        str_desc = "Initialize bot in this group"
        out_desc = "Leave with specified amount"
        quick_bet = "Quick Bet:"
        quick_bet_text = "Just send a number (e.g., `50`)"
        info_commands = "Information Commands:"
        sts_desc = "Show current table status"
        t_desc = "Show settlement transactions"
        v_desc = "Show bot version"
        mgmt_commands = "Management Commands:"
        u_desc = "Undo last bet"
        r_desc = "Reset all bets"
        h_desc = "Show this help"

        message = (
            "━━━━━━━━━━━━━\n"
            f"📚 *{header}* 📚\n"
            "━━━━━━━━━━━━━\n\n"
            f"🃏 *{poker_commands}*\n"
            f"  `str` — {str_desc}\n"
            f"  `out <amount>` — {out_desc}\n\n"
            f"  *{quick_bet}* {quick_bet_text}\n\n"
            f"📊 *{info_commands}*\n"
            f"  `s` — {sts_desc}\n"
            f"  `t` — {t_desc}\n"
            f"  `v` — {v_desc}\n\n"
            f"🔧 *{mgmt_commands}*\n"
            f"  `u` — {u_desc}\n"
            f"  `r` — {r_desc}\n"
            f"  `h` — {h_desc}\n\n"
            "━━━━━━━━━━━━━"
        )

        return message

    def format_welcome_message(self) -> str:
        """Format the welcome message when bot joins a group."""
        header = "WELCOME"
        joined = "Poker Bot has joined the group!"
        description = "I'll help you track poker bets and calculate fair settlements automatically."
        to_get_started = "To get started:"
        str_instruction = "Type `str` to initialize the bot"
        need_help = "Need help?"
        help_instruction = "Type `h` anytime"

        message = (
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

        return message
