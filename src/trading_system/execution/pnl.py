from decimal import Decimal

from trading_system.core.models.positions import Position


def unrealized_pnl(
    position: Position,
    mark_price: Decimal,
) -> Decimal:
    return position.unrealized_pnl(mark_price)


def total_pnl(
    position: Position,
    mark_price: Decimal,
) -> Decimal:
    return (
        position.realized_pnl
        + unrealized_pnl(position, mark_price)
    )