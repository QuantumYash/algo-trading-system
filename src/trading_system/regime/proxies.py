from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class MacroProxies:
    """Normalized macro/market proxies used by the regime engine."""

    volatility: Decimal | None = None
    trend_strength: Decimal | None = None
    market_return: Decimal | None = None
    volume_ratio: Decimal | None = None

    def __post_init__(self) -> None:
        if self.volatility is not None and self.volatility < 0:
            raise ValueError("volatility cannot be negative.")

        if self.trend_strength is not None and self.trend_strength < 0:
            raise ValueError("trend_strength cannot be negative.")

        if self.volume_ratio is not None and self.volume_ratio < 0:
            raise ValueError("volume_ratio cannot be negative.")