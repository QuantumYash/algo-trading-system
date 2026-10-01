from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from trading_system.core.enums import Side


@dataclass(frozen=True, slots=True)
class Fill:
    """An execution received from a broker or simulated broker."""

    fill_id: str
    order_id: str
    symbol: str
    side: Side
    quantity: int
    price: Decimal
    timestamp: datetime
    commission: Decimal = Decimal(0)
    taxes: Decimal = Decimal(0)

    @property
    def total_cost(self) -> Decimal:
        """Total execution value including charges."""
        gross_value = self.price * self.quantity
        return gross_value + self.commission + self.taxes
