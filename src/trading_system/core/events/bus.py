import asyncio
from collections import defaultdict
from collections.abc import Awaitable, Callable

from trading_system.core.events.base import Event

EventHandler = Callable[[Event], Awaitable[None]]


class EventBus:
    """
    Asynchronous publish/subscribe event bus.

    Components subscribe to event types and receive matching events.
    """

    def __init__(self) -> None:
        self._handlers: dict[type[Event], list[EventHandler]] = defaultdict(list)

    def subscribe(
        self,
        event_type: type[Event],
        handler: EventHandler,
    ) -> None:
        """Register an asynchronous handler for an event type."""

        self._handlers[event_type].append(handler)

    async def publish(self, event: Event) -> None:
        """Publish an event to all registered handlers."""

        handlers = self._handlers.get(type(event), [])

        if not handlers:
            return

        await asyncio.gather(*(handler(event) for handler in handlers))
