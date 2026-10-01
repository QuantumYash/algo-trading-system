from datetime import UTC, datetime
from decimal import Decimal

import pytest

from trading_system.core.events import EventBus, MarketEvent
from trading_system.core.models.market import Tick
from trading_system.data.normalizer import normalize_tick
from trading_system.data.pipeline import MarketDataPipeline
from trading_system.data.validator import validate_tick


def test_normalize_tick() -> None:
    timestamp = datetime.now(UTC)

    tick = normalize_tick(
        symbol="NIFTY",
        timestamp=timestamp,
        price=25000.50,
        volume=100,
        bid=25000.40,
        ask=25000.60,
    )

    assert tick.price == Decimal("25000.5")
    assert tick.volume == 100
    assert tick.bid == Decimal("25000.4")
    assert tick.ask == Decimal("25000.6")


def test_valid_tick() -> None:
    tick = Tick(
        symbol="NIFTY",
        timestamp=datetime.now(UTC),
        price=Decimal(25000),
        volume=100,
        bid=Decimal(24999),
        ask=Decimal(25001),
    )

    validate_tick(tick)


def test_invalid_price() -> None:
    tick = Tick(
        symbol="NIFTY",
        timestamp=datetime.now(UTC),
        price=Decimal(-1),
    )

    with pytest.raises(ValueError, match="price must be positive"):
        validate_tick(tick)


def test_invalid_bid_ask() -> None:
    tick = Tick(
        symbol="NIFTY",
        timestamp=datetime.now(UTC),
        price=Decimal(25000),
        bid=Decimal(25010),
        ask=Decimal(25000),
    )

    with pytest.raises(ValueError, match="Bid price cannot exceed ask"):
        validate_tick(tick)


@pytest.mark.asyncio
async def test_market_data_pipeline() -> None:
    event_bus = EventBus()
    pipeline = MarketDataPipeline(event_bus)

    received: list[MarketEvent] = []

    async def handler(event: MarketEvent) -> None:
        received.append(event)

    event_bus.subscribe(MarketEvent, handler)

    tick = Tick(
        symbol="NIFTY",
        timestamp=datetime.now(UTC),
        price=Decimal(25000),
        volume=100,
    )

    await pipeline.process_tick(tick)

    assert len(received) == 1
    assert received[0].symbol == "NIFTY"
    assert received[0].data == tick
