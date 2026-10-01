from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import uuid4

from trading_system.core.enums import OrderStatus
from trading_system.core.models.orders import Order, OrderIntent
from trading_system.core.models.positions import Position
from trading_system.execution.broker.base import BrokerAdapter


class PaperBroker(BrokerAdapter):
    """Deterministic in-memory broker for testing and paper trading."""

    def __init__(self) -> None:
        self._orders: dict[str, Order] = {}
        self._positions: dict[str, Position] = {}

    async def submit_order(self, intent: OrderIntent) -> Order:
        now = datetime.now(UTC)

        order_id = f"PAPER-{uuid4().hex[:12]}"

        order = Order(
            order_id=order_id,
            client_order_id="",
            symbol=intent.symbol,
            side=intent.side,
            quantity=intent.quantity,
            order_type=intent.order_type,
            status=OrderStatus.OPEN,
            limit_price=intent.limit_price,
            stop_price=intent.stop_price,
            created_at=now,
            updated_at=now,
        )

        self._orders[order_id] = order

        return order

    async def cancel_order(self, order_id: str) -> None:
        order = self._orders[order_id]

        if order.status in {
            OrderStatus.FILLED,
            OrderStatus.CANCELLED,
            OrderStatus.REJECTED,
        }:
            return

        order.status = OrderStatus.CANCELLED
        order.updated_at = datetime.now(UTC)

    async def get_order(self, order_id: str) -> Order:
        return self._orders[order_id]

    async def get_open_orders(self) -> Sequence[Order]:
        return tuple(
            order
            for order in self._orders.values()
            if order.status
            in {
                OrderStatus.OPEN,
                OrderStatus.PENDING,
                OrderStatus.PARTIALLY_FILLED,
            }
        )

    async def get_positions(self) -> Sequence[Position]:
        return tuple(self._positions.values())