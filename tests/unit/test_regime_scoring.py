
from decimal import Decimal

from trading_system.regime.proxies import MacroProxies
from trading_system.regime.scoring import calculate_regime_score


def test_regime_score_calculates_trend() -> None:
    score = calculate_regime_score(
        MacroProxies(
            trend_strength=Decimal("2.5"),
        )
    )

    assert score.trend_score == Decimal("2.5")


def test_negative_return_increases_risk_score() -> None:
    score = calculate_regime_score(
        MacroProxies(
            market_return=Decimal("-0.05"),
        )
    )

    assert score.risk_score == Decimal("0.05")


def test_high_volume_increases_risk_score() -> None:
    score = calculate_regime_score(
        MacroProxies(
            volume_ratio=Decimal("2.5"),
        )
    )

    assert score.risk_score == Decimal(1)


def test_neutral_proxies_produce_zero_scores() -> None:
    score = calculate_regime_score(
        MacroProxies()
    )

    assert score.trend_score == Decimal(0)
    assert score.volatility_score == Decimal(0)
    assert score.risk_score == Decimal(0)