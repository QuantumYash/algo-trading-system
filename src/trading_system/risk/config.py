
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class RiskConfig:
    """Global risk limits for order approval."""

    max_position_quantity: int = 10
    max_order_quantity: int = 5
    max_notional: Decimal = Decimal(100000)
    daily_loss_limit: Decimal = Decimal(5000)
    kill_switch: bool = False

    def __post_init__(self) -> None:
        if self.max_position_quantity <= 0:
            raise ValueError("max_position_quantity must be positive.")

        if self.max_order_quantity <= 0:
            raise ValueError("max_order_quantity must be positive.")

        if self.max_order_quantity > self.max_position_quantity:
            raise ValueError(
                "max_order_quantity cannot exceed max_position_quantity."
            )

        if self.max_notional <= 0:
            raise ValueError("max_notional must be positive.")

        if self.daily_loss_limit <= 0:
            raise ValueError("daily_loss_limit must be positive.")
            