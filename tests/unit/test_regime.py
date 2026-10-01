from datetime import UTC, datetime
from decimal import Decimal

from trading_system.core.models.market import Bar
from trading_system.indicators.snapshot import IndicatorSnapshot
from trading_system.regime import (
    MacroRegimeEngine,
    MarketRegime,
    RegimeAction,
)


def make_bar() -> Bar:
    price = Decimal(100)

    return Bar(
        symbol="TEST",
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        open=price,
        high=Decimal(102),
        low=Decimal(98),
        close=price,
        volume=100,
    )


def test_regime_engine_detects_trending_market() -> None:
    indicators = IndicatorSnapshot(
        ema_fast=Decimal(105),
        ema_slow=Decimal(100),
        rsi=Decimal(60),
        atr=Decimal(2),
        vwap=Decimal(102),
    )

    engine = MacroRegimeEngine()

    snapshot = engine.evaluate(make_bar(), indicators)

    assert snapshot.regime == MarketRegime.TRENDING
    assert snapshot.action == RegimeAction.ALLOW
    assert snapshot.allow_new_entries is True
    assert snapshot.grid_spacing_multiplier == Decimal("1.25")


def test_regime_engine_handles_warmup() -> None:
    indicators = IndicatorSnapshot(
        ema_fast=None,
        ema_slow=None,
        rsi=None,
        atr=None,
        vwap=None,
    )

    engine = MacroRegimeEngine()

    snapshot = engine.evaluate(make_bar(), indicators)

    assert snapshot.regime == MarketRegime.NORMAL
    assert snapshot.allow_new_entries is True
    assert snapshot.reason == "Indicator warm-up period."


def test_regime_engine_series_requires_matching_lengths() -> None:
    engine = MacroRegimeEngine()

    bar = make_bar()

    indicators = IndicatorSnapshot(
        ema_fast=Decimal(100),
        ema_slow=Decimal(100),
        rsi=Decimal(50),
        atr=Decimal(2),
        vwap=Decimal(100),
    )

    try:
        engine.evaluate_series([bar, bar], [indicators])
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Expected ValueError for mismatched lengths."
        )