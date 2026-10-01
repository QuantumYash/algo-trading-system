from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class RegimeThresholds:
    high_volatility: Decimal = Decimal(2)
    low_volatility: Decimal = Decimal("0.5")
    strong_trend: Decimal = Decimal(1)
    risk_off: Decimal = Decimal(1)

    def __post_init__(self) -> None:
        if self.high_volatility <= 0:
            raise ValueError("high_volatility must be positive.")

        if self.low_volatility < 0:
            raise ValueError("low_volatility cannot be negative.")

        if self.strong_trend < 0:
            raise ValueError("strong_trend cannot be negative.")

        if self.risk_off < 0:
            raise ValueError("risk_off cannot be negative.")