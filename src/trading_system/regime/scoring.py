from dataclasses import dataclass
from decimal import Decimal

from trading_system.regime.proxies import MacroProxies


@dataclass(frozen=True, slots=True)
class RegimeScore:
    """Scores produced from normalized macro proxies."""

    trend_score: Decimal
    volatility_score: Decimal
    risk_score: Decimal


def calculate_regime_score(
    proxies: MacroProxies,
) -> RegimeScore:
    trend_score = Decimal(0)
    volatility_score = Decimal(0)
    risk_score = Decimal(0)

    if proxies.trend_strength is not None:
        trend_score += proxies.trend_strength

    if proxies.volatility is not None:
        volatility_score = proxies.volatility

    if (
        proxies.market_return is not None
        and proxies.market_return < Decimal(0)
    ):
        risk_score += abs(proxies.market_return)

    if (
        proxies.volume_ratio is not None
        and proxies.volume_ratio > Decimal(2)
    ):
        risk_score += Decimal(1)

    return RegimeScore(
        trend_score=trend_score,
        volatility_score=volatility_score,
        risk_score=risk_score,
    )