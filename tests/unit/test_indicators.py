from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from trading_system.core.models.market import Bar
from trading_system.indicators.engine import IndicatorEngine
from trading_system.indicators.momentum import rsi
from trading_system.indicators.trend import ema
from trading_system.indicators.volatility import atr
from trading_system.indicators.volume import vwap


def make_bars(
    closes: list[int],
) -> list[Bar]:
    bars: list[Bar] = []

    start = datetime(
        2026,
        1,
        1,
        tzinfo=UTC,
    )

    for index, close in enumerate(closes):
        price = Decimal(close)

        bars.append(
            Bar(
                symbol="TEST",
                timestamp=start + timedelta(
                    minutes=index
                ),
                open=price - Decimal(1),
                high=price + Decimal(1),
                low=price - Decimal(1),
                close=price,
                volume=100,
            )
        )

    return bars


def test_ema_requires_enough_values() -> None:
    values = [
        Decimal(100),
        Decimal(101),
    ]

    result = ema(values, period=3)

    assert result == [None, None]


def test_ema_seed_value() -> None:
    values = [
        Decimal(10),
        Decimal(11),
        Decimal(12),
    ]

    result = ema(values, period=3)

    assert result[0] is None
    assert result[1] is None
    assert result[2] == Decimal(11)


def test_rsi_returns_100_for_only_gains() -> None:
    closes = [
        Decimal(100),
        Decimal(101),
        Decimal(102),
        Decimal(103),
        Decimal(104),
    ]

    result = rsi(
        closes,
        period=3,
    )

    assert result[0] is None
    assert result[1] is None
    assert result[2] is None
    assert result[3] == Decimal(100)


def test_atr_uses_true_range() -> None:
    bars = make_bars(
        [100, 102, 101]
    )

    result = atr(
        bars,
        period=2,
    )

    assert result[0] is None
    assert result[1] is not None


def test_vwap_calculation() -> None:
    bars = make_bars(
        [100, 110]
    )

    result = vwap(bars)

    assert result[0] is not None
    assert result[1] is not None

    expected_first = Decimal(100)

    assert result[0] == expected_first


def test_indicator_engine() -> None:
    bars = make_bars(
        list(range(1, 31))
    )

    engine = IndicatorEngine()

    snapshots = engine.calculate(bars)

    assert len(snapshots) == 30

    latest = snapshots[-1]

    assert latest.ema_fast is not None
    assert latest.ema_slow is not None
    assert latest.rsi is not None
    assert latest.atr is not None
    assert latest.vwap is not None


def test_indicator_engine_rejects_invalid_periods() -> None:
    with pytest.raises(ValueError):
        IndicatorEngine(
            ema_fast_period=26,
            ema_slow_period=12,
        )


def test_indicator_engine_latest_requires_bars() -> None:
    engine = IndicatorEngine()

    with pytest.raises(ValueError):
        engine.latest([])