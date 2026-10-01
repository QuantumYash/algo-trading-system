import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from trading_system.core.events import BarEvent, EventBus
from trading_system.core.models.market import Tick
from trading_system.data.aggregator import BarAggregator
from trading_system.data.runtime import MarketDataRuntime


def make_tick(
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
            0,
            second,
            tzinfo=UTC,
        ),
        price=Decimal(price),
        volume=volume,
    )


@pytest.mark.asyncio
async def test_runtime_publishes_bar_event() -> None:
    bus = EventBus()
    received: list[BarEvent] = []

    async def handler(event: BarEvent) -> None:
        received.append(event)

    bus.subscribe(BarEvent, handler)

    runtime = MarketDataRuntime(
        event_bus=bus,
        aggregator=BarAggregator(
            interval=timedelta(minutes=1),
        ),
    )

    await runtime.start()

    await runtime.submit(make_tick(1, "100"))
    await runtime.submit(make_tick(30, "105"))

    await runtime.flush()
    await runtime.shutdown()

    assert len(received) == 1
    assert received[0].symbol == "TEST"
    assert received[0].data.close == Decimal(105)
    assert runtime.ticks_processed == 2
    assert runtime.bars_published == 1


@pytest.mark.asyncio
async def test_runtime_has_bounded_queue() -> None:
    bus = EventBus()

    runtime = MarketDataRuntime(
        event_bus=bus,
        aggregator=BarAggregator(),
        queue_size=2,
    )

    assert runtime.queue_size == 2
    assert runtime.pending_ticks == 0

    await runtime.start()

    await runtime.submit(make_tick(1, "100"))
    await runtime.submit(make_tick(2, "101"))

    await asyncio.wait_for(
        runtime._queue.join(),
        timeout=1.0,
    )

    assert runtime.pending_ticks == 0
    assert runtime.ticks_processed == 2

    await runtime.shutdown()


@pytest.mark.asyncio
async def test_runtime_rejects_invalid_tick() -> None:
    bus = EventBus()

    runtime = MarketDataRuntime(
        event_bus=bus,
        aggregator=BarAggregator(),
    )

    await runtime.start()

    invalid_tick = Tick(
        symbol="TEST",
        timestamp=datetime(
            2026,
            1,
            1,
            10,
            0,
            0,
            tzinfo=UTC,
        ),
        price=Decimal(-100),
    )

    with pytest.raises(ValueError, match="positive"):
        await runtime.submit(invalid_tick)

    assert runtime.ticks_rejected == 1

    await runtime.shutdown()


@pytest.mark.asyncio
async def test_runtime_rejects_submit_after_shutdown() -> None:
    bus = EventBus()

    runtime = MarketDataRuntime(
        event_bus=bus,
        aggregator=BarAggregator(),
    )

    await runtime.start()
    await runtime.shutdown()

    with pytest.raises(RuntimeError, match="shutdown"):
        await runtime.submit(make_tick(1, "100"))


@pytest.mark.asyncio
async def test_runtime_consumes_async_stream() -> None:
    bus = EventBus()
    received: list[BarEvent] = []

    async def handler(event: BarEvent) -> None:
        received.append(event)

    bus.subscribe(BarEvent, handler)

    runtime = MarketDataRuntime(
        event_bus=bus,
        aggregator=BarAggregator(
            interval=timedelta(minutes=1),
        ),
    )

    async def stream():
        yield make_tick(1, "100")
        yield make_tick(30, "110")

    await runtime.consume(stream())
    await runtime.flush()

    assert len(received) == 1
    assert received[0].data.close == Decimal(110)
    assert runtime.ticks_processed == 2
    assert runtime.bars_published == 1