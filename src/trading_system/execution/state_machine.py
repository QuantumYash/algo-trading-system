
from trading_system.core.enums import OrderStatus

VALID_TRANSITIONS: dict[OrderStatus, frozenset[OrderStatus]] = {
    OrderStatus.CREATED: frozenset(
        {
            OrderStatus.PENDING,
            OrderStatus.REJECTED,
        }
    ),
    OrderStatus.PENDING: frozenset(
        {
            OrderStatus.OPEN,
            OrderStatus.FILLED,
            OrderStatus.REJECTED,
            OrderStatus.CANCEL_PENDING,
        }
    ),
    OrderStatus.OPEN: frozenset(
        {
            OrderStatus.PARTIALLY_FILLED,
            OrderStatus.FILLED,
            OrderStatus.CANCEL_PENDING,
            OrderStatus.CANCELLED,
            OrderStatus.REJECTED,
        }
    ),
    OrderStatus.PARTIALLY_FILLED: frozenset(
        {
            OrderStatus.PARTIALLY_FILLED,
            OrderStatus.FILLED,
            OrderStatus.CANCEL_PENDING,
            OrderStatus.CANCELLED,
        }
    ),
    OrderStatus.CANCEL_PENDING: frozenset(
        {
            OrderStatus.CANCELLED,
            OrderStatus.FILLED,
        }
    ),
    OrderStatus.FILLED: frozenset(),
    OrderStatus.CANCELLED: frozenset(),
    OrderStatus.REJECTED: frozenset(),
}


class InvalidOrderTransition(ValueError):
    """Raised when an invalid order lifecycle transition is attempted."""


def validate_transition(
    current: OrderStatus,
    new: OrderStatus,
) -> None:
    if new not in VALID_TRANSITIONS[current]:
        raise InvalidOrderTransition(
            f"Invalid order transition: {current} -> {new}"
        )