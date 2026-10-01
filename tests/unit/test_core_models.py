from datetime import UTC, datetime
from decimal import Decimal

from trading_system.core.enums import OrderStatus, OrderType, Side
from trading_system.core.models import (
    Bar,
    Fill,
    Order,
    OrderIntent,
    Position,
    Tick,
)


def test_tick_creation() -> None:
    tick = Tick(
        symbol="NIFTY",
        timestamp=datetime.now(UTC),
        price=Decimal("25000.50"),
        volume=100,
    )

    assert tick.symbol == "NIFTY"
    assert tick.price == Decimal("25000.50")
    assert tick.volume == 100


def test_bar_creation() -> None:
    bar = Bar(
        symbol="NIFTY",
        timestamp=datetime.now(UTC),
        open=Decimal(25000),
        high=Decimal(25100),
        low=Decimal(24950),
        close=Decimal(25050),
        volume=10000,
    )

    assert bar.high >= bar.open
    assert bar.high >= bar.close
    assert bar.low <= bar.open
    assert bar.low <= bar.close


def test_order_intent() -> None:
    intent = OrderIntent(
        symbol="NIFTY",
        side=Side.BUY,
        quantity=50,
        order_type=OrderType.MARKET,
        strategy_id="grid_v1",
        reason="grid_level_1",
    )

    assert intent.side == Side.BUY
    assert intent.quantity == 50
    assert intent.strategy_id == "grid_v1"


def test_order_defaults() -> None:
    order = Order(
        order_id="ORD-001",
        client_order_id="CLIENT-001",
        symbol="NIFTY",
        side=Side.BUY,
        quantity=50,
        order_type=OrderType.MARKET,
    )

    assert order.status == OrderStatus.CREATED
    assert order.filled_quantity == 0


def test_fill_total_cost() -> None:
    fill = Fill(
        fill_id="FILL-001",
        order_id="ORD-001",
        symbol="NIFTY",
        side=Side.BUY,
        quantity=50,
        price=Decimal(25000),
        timestamp=datetime.now(UTC),
        commission=Decimal(10),
        taxes=Decimal(5),
    )

    assert fill.total_cost == Decimal(1250015)


def test_long_position_unrealized_pnl() -> None:
    position = Position(
        symbol="NIFTY",
        quantity=50,
        average_price=Decimal(25000),
    )

    assert position.unrealized_pnl(Decimal(25010)) == Decimal(500)


def test_short_position_unrealized_pnl() -> None:
    position = Position(
        symbol="NIFTY",
        quantity=-50,
        average_price=Decimal(25000),
    )

    assert position.unrealized_pnl(Decimal(24990)) == Decimal(500)
