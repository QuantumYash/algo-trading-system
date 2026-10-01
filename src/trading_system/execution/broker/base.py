
from abc import ABC, abstractmethod
from collections.abc import Sequence

from trading_system.core.models.orders import Order, OrderIntent
from trading_system.core.models.positions import Position


class BrokerError(Exception):
    """Base broker exception."""


class TransientBrokerError(BrokerError):
    """Temporary broker failure that can be retried."""


class PermanentBrokerError(BrokerError):
    """Broker failure that should not be retried."""


class BrokerAdapter(ABC):
    """Abstract interface implemented by paper/live brokers."""

    @abstractmethod
    async def submit_order(self, intent: OrderIntent) -> Order:
        raise NotImplementedError

    @abstractmethod
    async def cancel_order(self, order_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_order(self, order_id: str) -> Order:
        raise NotImplementedError

    @abstractmethod
    async def get_open_orders(self) -> Sequence[Order]:
        raise NotImplementedError

    @abstractmethod
    async def get_positions(self) -> Sequence[Position]:
        raise NotImplementedError