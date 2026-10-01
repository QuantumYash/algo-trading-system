from dataclasses import dataclass
from decimal import Decimal

from trading_system.regime.enums import MarketRegime, RegimeAction


@dataclass(frozen=True, slots=True)
class RegimeSnapshot:
    """Immutable description of the current market regime."""

    regime: MarketRegime
    action: RegimeAction

    volatility_multiplier: Decimal
    position_multiplier: Decimal
    grid_spacing_multiplier: Decimal

    allow_new_entries: bool
    reason: str