
from dataclasses import dataclass
from decimal import Decimal

from trading_system.core.models.orders import OrderIntent


@dataclass(frozen=True, slots=True)
class RiskDecision:
    """Result of risk evaluation."""

    approved: bool
    intents: tuple[OrderIntent, ...]
    reason: str
    projected_position: int
    projected_notional: Decimal


@dataclass(frozen=True, slots=True)
class RiskState:
    """Current account-level risk state."""

    daily_pnl: Decimal = Decimal(0)
    kill_switch: bool = False