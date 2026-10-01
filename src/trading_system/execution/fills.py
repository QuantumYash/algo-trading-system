from datetime import UTC, datetime
from decimal import Decimal

from trading_system.core.models.fills import Fill
from trading_system.core.models.orders import Order


def create_fill(
    order: Order,
    price: Decimal,
    quantity: int | None = None,
    commission: Decimal = Decimal(0),
    taxes: Decimal = Decimal(0),
) -> Fill:
    fill_quantity = quantity if quantity is not None else order.quantity

    if fill_quantity <= 0:
        raise ValueError("Fill quantity must be positive.")

    remaining_quantity = order.quantity - order.filled_quantity

    if fill_quantity > remaining_quantity:
        raise ValueError(
            "Fill quantity exceeds remaining order quantity."
        )

    if price <= 0:
        raise ValueError("Fill price must be positive.")

    if commission < 0:
        raise ValueError("Commission cannot be negative.")

    if taxes < 0:
        raise ValueError("Taxes cannot be negative.")

    return Fill(
        fill_id=f"FILL-{order.order_id}-{order.filled_quantity + fill_quantity}",
        order_id=order.order_id,
        symbol=order.symbol,
        side=order.side,
        quantity=fill_quantity,
        price=price,
        timestamp=datetime.now(UTC),
        commission=commission,
        taxes=taxes,
    )