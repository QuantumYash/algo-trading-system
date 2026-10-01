from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from trading_system.core.models.market import Tick


class MarketDataAdapter(ABC):
    """Interface for live and historical market-data providers."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish a connection to the market-data source."""
        raise NotImplementedError

    @abstractmethod
    async def disconnect(self) -> None:
        """Close the market-data connection."""
        raise NotImplementedError

    @abstractmethod
    async def stream(self) -> AsyncIterator[Tick]:
        """Yield normalized ticks from the market-data source."""
        raise NotImplementedError