"""User-related utility functions."""

from telegram import User


def get_display_name(user: User) -> str:
    """Get display name from Telegram user object.

    Prioritizes first_name + last_name (display name) over @username.

    Args:
        user: Telegram User object

    Returns:
        Display name string
    """
    if user.first_name:
        name = user.first_name
        if user.last_name:
            name += f" {user.last_name}"
        return name
    if user.username:
        return user.username
    return f"User{user.id}"
