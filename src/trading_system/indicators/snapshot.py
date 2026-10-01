from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class IndicatorSnapshot:
    """Indicator values corresponding to one bar."""

    ema_fast: Decimal | None
    ema_slow: Decimal | None
    rsi: Decimal | None
    atr: Decimal | None
    vwap: Decimal | None