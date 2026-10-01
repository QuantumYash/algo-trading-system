from dataclasses import dataclass
from decimal import Decimal

from trading_system.core.enums import Side
from trading_system.core.models.orders import OrderIntent
from trading_system.core.models.positions import Position
from trading_system.indicators.snapshot import IndicatorSnapshot
from trading_system.regime.models import RegimeSnapshot


@dataclass(frozen=True, slots=True)
class StrategyContext:
    """All state required by a strategy for one decision."""

    symbol: str
    price: Decimal
    indicators: IndicatorSnapshot
    regime: RegimeSnapshot
    position: Position


@dataclass(frozen=True, slots=True)
class GridLevel:
    """One price level in the trading grid."""

    price: Decimal
    side: Side
    level: int


@dataclass(frozen=True, slots=True)
class StrategyDecision:
    """Result produced by a strategy."""

    intents: tuple[OrderIntent, ...]
    reason: str