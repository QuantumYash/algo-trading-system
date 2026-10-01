from enum import StrEnum


class MarketRegime(StrEnum):
    NORMAL = "NORMAL"
    TRENDING = "TRENDING"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    LOW_VOLATILITY = "LOW_VOLATILITY"
    RISK_OFF = "RISK_OFF"


class RegimeAction(StrEnum):
    ALLOW = "ALLOW"
    REDUCE = "REDUCE"
    BLOCK = "BLOCK"