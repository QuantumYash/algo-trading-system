from trading_system.core.events import EventBus, MarketEvent
from trading_system.core.models.market import Tick
from trading_system.data.validator import validate_tick


class MarketDataPipeline:
    """Validate market data and publish it to the event bus."""

    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus

    async def process_tick(self, tick: Tick) -> None:
        """Validate and publish a tick."""

        validate_tick(tick)

        event = MarketEvent(
            timestamp=tick.timestamp,
            symbol=tick.symbol,
            data=tick,
        )

        await self._event_bus.publish(event)
