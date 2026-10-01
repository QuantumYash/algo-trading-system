from datetime import UTC, datetime, timedelta
from decimal import Decimal

from trading_system.core.models.market import Tick
from trading_system.data.aggregator import BarAggregator


def make_tick(
    minute: int,
    second: int,
    price: str,
    volume: int = 10,
) -> Tick:
    return Tick(
        symbol="TEST",
        timestamp=datetime(
            2026,
            1,
            1,
            10,
            minute,
            second,
            tzinfo=UTC,
        ),
        price=Decimal(price),
        volume=volume,
    )


def test_aggregator_builds_ohlcv_bar() -> None:
    aggregator = BarAggregator(
        interval=timedelta(minutes=1),
    )

    assert aggregator.process_tick(
        make_tick(0, 1, "100", 10)
    ) == []

    assert aggregator.process_tick(
        make_tick(0, 20, "105", 20)
    ) == []

    bars = aggregator.process_tick(
        make_tick(1, 1, "110", 30)
    )

    assert len(bars) == 1

    bar = bars[0]

    assert bar.symbol == "TEST"
    assert bar.open == Decimal(100)
    assert bar.high == Decimal(105)
    assert bar.low == Decimal(100)
    assert bar.close == Decimal(105)
    assert bar.volume == 30


def test_aggregator_handles_multiple_bars() -> None:
    aggregator = BarAggregator(
        interval=timedelta(minutes=1),
    )

    aggregator.process_tick(
        make_tick(0, 10, "100")
    )

    bars = aggregator.process_tick(
        make_tick(1, 10, "110")
    )

    assert len(bars) == 1
    assert bars[0].close == Decimal(100)

    bars = aggregator.process_tick(
        make_tick(2, 10, "120")
    )

    assert len(bars) == 1
    assert bars[0].close == Decimal(110)

    remaining_bars = aggregator.flush()

    assert len(remaining_bars) == 1
    assert remaining_bars[0].close == Decimal(120)


def test_aggregator_flushes_remaining_bar() -> None:
    aggregator = BarAggregator(
        interval=timedelta(minutes=1),
    )

    aggregator.process_tick(
        make_tick(0, 10, "100")
    )

    bars = aggregator.flush()

    assert len(bars) == 1
    assert bars[0].open == Decimal(100)
    assert bars[0].close == Decimal(100)
    assert bars[0].volume == 10


def test_aggregator_rejects_naive_timestamp() -> None:
    aggregator = BarAggregator()

    tick = Tick(
        symbol="TEST",
        timestamp=datetime(2026, 1, 1, 10, 0, 0),  # noqa: DTZ001
        price=Decimal(100),
        volume=10,
    )

    try:
        aggregator.process_tick(tick)
    except ValueError as exc:
        assert "timezone-aware" in str(exc)
    else:
        raise AssertionError(
            "Expected naive timestamp to be rejected."
        )