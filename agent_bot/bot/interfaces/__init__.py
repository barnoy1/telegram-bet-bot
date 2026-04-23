"""Interface definitions for bot components."""

from .command_handler import ICommandHandler
from .settlement_service import ISettlementService
from .group_service import IGroupService

__all__ = ["ICommandHandler", "ISettlementService", "IGroupService"]
