from datetime import UTC, datetime

import pytest

from trading_system.core.events import EventBus, MarketEvent


@pytest.mark.asyncio
async def test_event_bus_delivers_event() -> None:
    bus = EventBus()

    received: list[MarketEvent] = []

    async def handler(event: MarketEvent) -> None:
        received.append(event)

    bus.subscribe(MarketEvent, handler)

    event = MarketEvent(
        timestamp=datetime.now(UTC),
        symbol="NIFTY",
        data={"price": 25000},
    )

    await bus.publish(event)

    assert len(received) == 1
    assert received[0].symbol == "NIFTY"
    assert received[0].data["price"] == 25000


@pytest.mark.asyncio
async def test_event_bus_supports_multiple_handlers() -> None:
    bus = EventBus()

    first_handler_called = False
    second_handler_called = False

    async def first_handler(event: MarketEvent) -> None:
        nonlocal first_handler_called
        first_handler_called = True

    async def second_handler(event: MarketEvent) -> None:
        nonlocal second_handler_called
        second_handler_called = True

    bus.subscribe(MarketEvent, first_handler)
    bus.subscribe(MarketEvent, second_handler)

    event = MarketEvent(
        timestamp=datetime.now(UTC),
        symbol="NIFTY",
        data={"price": 25000},
    )

    await bus.publish(event)

    assert first_handler_called
    assert second_handler_called


@pytest.mark.asyncio
async def test_event_without_handler_is_safe() -> None:
    bus = EventBus()

    event = MarketEvent(
        timestamp=datetime.now(UTC),
        symbol="NIFTY",
        data={"price": 25000},
    )

    await bus.publish(event)
