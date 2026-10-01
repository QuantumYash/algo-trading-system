from decimal import Decimal

import pytest

from trading_system.core.enums import OrderStatus, OrderType, Side
from trading_system.core.models.orders import OrderIntent
from trading_system.execution.broker.paper import PaperBroker


@pytest.mark.asyncio
async def test_submit_order() -> None:
    broker = PaperBroker()

    intent = OrderIntent(
        symbol="NIFTY",
        side=Side.BUY,
        quantity=1,
        order_type=OrderType.LIMIT,
        limit_price=Decimal(25000),
    )

    order = await broker.submit_order(intent)

    assert order.order_id.startswith("PAPER-")
    assert order.symbol == "NIFTY"
    assert order.side == Side.BUY
    assert order.quantity == 1
    assert order.status == OrderStatus.OPEN


@pytest.mark.asyncio
async def test_get_open_orders() -> None:
    broker = PaperBroker()

    intent = OrderIntent(
        symbol="NIFTY",
        side=Side.BUY,
        quantity=1,
    )

    order = await broker.submit_order(intent)

    orders = await broker.get_open_orders()

    assert len(orders) == 1
    assert orders[0].order_id == order.order_id


@pytest.mark.asyncio
async def test_cancel_order() -> None:
    broker = PaperBroker()

    intent = OrderIntent(
        symbol="NIFTY",
        side=Side.BUY,
        quantity=1,
    )

    order = await broker.submit_order(intent)

    await broker.cancel_order(order.order_id)

    cancelled = await broker.get_order(order.order_id)

    assert cancelled.status == OrderStatus.CANCELLED