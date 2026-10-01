from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from trading_system.core.enums import OrderStatus, OrderType, Side


@dataclass(frozen=True, slots=True)
class OrderIntent:
    """
    Strategy-generated request to trade.

    This is NOT a broker order.
    It must pass through the risk engine first.
    """

    symbol: str
    side: Side
    quantity: int
    order_type: OrderType = OrderType.MARKET
    limit_price: Decimal | None = None
    stop_price: Decimal | None = None
    strategy_id: str = ""
    reason: str = ""


@dataclass(slots=True)
class Order:
    """An executable order tracked by the order manager."""

    order_id: str
    client_order_id: str
    symbol: str
    side: Side
    quantity: int
    order_type: OrderType
    status: OrderStatus = OrderStatus.CREATED
    limit_price: Decimal | None = None
    stop_price: Decimal | None = None
    filled_quantity: int = 0
    average_fill_price: Decimal | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
