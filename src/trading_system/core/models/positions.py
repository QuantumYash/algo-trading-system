from dataclasses import dataclass
from decimal import Decimal

from trading_system.core.enums import PositionSide


@dataclass(slots=True)
class Position:
    """Current position for one instrument."""

    symbol: str
    quantity: int = 0
    average_price: Decimal = Decimal(0)
    realized_pnl: Decimal = Decimal(0)

    @property
    def side(self) -> PositionSide:
        if self.quantity > 0:
            return PositionSide.LONG

        if self.quantity < 0:
            return PositionSide.SHORT

        return PositionSide.FLAT

    @property
    def absolute_quantity(self) -> int:
        return abs(self.quantity)

    def unrealized_pnl(self, mark_price: Decimal) -> Decimal:
        if self.quantity == 0:
            return Decimal(0)

        return (mark_price - self.average_price) * self.quantity
