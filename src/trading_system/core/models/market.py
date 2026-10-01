from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class Tick:
    """A single market-data update."""

    symbol: str
    timestamp: datetime
    price: Decimal
    volume: int = 0
    bid: Decimal | None = None
    ask: Decimal | None = None


@dataclass(frozen=True, slots=True)
class Bar:
    """OHLCV market-data bar."""

    symbol: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
