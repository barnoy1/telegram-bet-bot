"""Mock LLM personality service for testing."""

from typing import Optional


class MockLLMPersonalityService:
    """Mock LLM service that returns predictable responses for testing."""

    def __init__(self):
        """Initialize mock service with no real LLM connection."""
        self.call_log = []  # Track which methods were called

    async def _generate_response(self, prompt: str) -> Optional[str]:
        """Return a mock response instead of calling LLM."""
        self.call_log.append(("generate", prompt))
        return f"Mock response for: {prompt[:50]}..."

    async def get_rebuy_response(self, username: str) -> Optional[str]:
        """Mock rebuy response."""
        self.call_log.append(("rebuy", username))
        return f"Mock rebuy taunt for {username}"

    async def get_bet_response(self, username: str, amount: float) -> Optional[str]:
        """Mock bet response."""
        self.call_log.append(("bet", username, amount))
        return f"Mock bet taunt for {username} betting {amount}"

    async def get_out_response(self, username: str, balance: float) -> Optional[str]:
        """Mock out response."""
        self.call_log.append(("out", username, balance))
        return f"Mock out taunt for {username} with balance {balance}"

    async def get_big_takeover_response(self, username: str, amount: float, pot_percentage: float) -> Optional[str]:
        """Mock big takeover response."""
        self.call_log.append(("big_takeover", username, amount, pot_percentage))
        return f"Mock big takeover taunt for {username}"

    async def get_big_cashout_response(self, username: str, amount: float, pot_percentage: float) -> Optional[str]:
        """Mock big cashout response."""
        self.call_log.append(("big_cashout", username, amount, pot_percentage))
        return f"Mock big cashout taunt for {username}"

    def was_called(self, method_name: str) -> bool:
        """Check if a specific method was called."""
        return any(call[0] == method_name for call in self.call_log)

    def clear_log(self):
        """Clear the call log."""
        self.call_log = []
