import asyncio
from collections.abc import AsyncIterator

from trading_system.core.events import BarEvent, EventBus
from trading_system.core.models.market import Bar, Tick
from trading_system.data.aggregator import BarAggregator
from trading_system.data.validator import validate_tick


class MarketDataRuntime:
    """
    Asynchronous runtime for processing market-data ticks.

    Architecture:

        producer
            |
            v
        bounded queue
            |
            v
        single consumer
            |
            v
        BarAggregator
            |
            v
        BarEvent
            |
            v
        EventBus

    The producer receives ticks.

    The consumer owns the stateful BarAggregator. This single-writer
    design minimizes race conditions around aggregation state.
    """

    def __init__(
        self,
        event_bus: EventBus,
        aggregator: BarAggregator,
        queue_size: int = 10_000,
    ) -> None:
        if queue_size <= 0:
            raise ValueError("queue_size must be positive.")

        self._event_bus = event_bus
        self._aggregator = aggregator

        self._queue: asyncio.Queue[Tick | None] = asyncio.Queue(
            maxsize=queue_size
        )

        self._shutdown = asyncio.Event()
        self._consumer_task: asyncio.Task[None] | None = None

        self._ticks_processed = 0
        self._ticks_rejected = 0
        self._bars_published = 0

    @property
    def queue_size(self) -> int:
        """Maximum number of ticks buffered in memory."""
        return self._queue.maxsize

    @property
    def pending_ticks(self) -> int:
        """Number of ticks currently waiting for processing."""
        return self._queue.qsize()

    @property
    def ticks_processed(self) -> int:
        """Number of successfully processed ticks."""
        return self._ticks_processed

    @property
    def ticks_rejected(self) -> int:
        """Number of ticks rejected during validation."""
        return self._ticks_rejected

    @property
    def bars_published(self) -> int:
        """Number of finalized bars published as events."""
        return self._bars_published

    @property
    def is_running(self) -> bool:
        """Whether the consumer task is currently running."""
        return (
            self._consumer_task is not None
            and not self._consumer_task.done()
        )

    @property
    def is_shutdown(self) -> bool:
        """Whether shutdown has been requested."""
        return self._shutdown.is_set()

    async def start(self) -> None:
        """
        Start the single consumer task.

        Calling start() multiple times is safe.
        """
        if self.is_running:
            return

        if self._shutdown.is_set():
            raise RuntimeError(
                "Cannot start runtime after shutdown."
            )

        self._consumer_task = asyncio.create_task(
            self.run(),
            name="market-data-runtime",
        )

    async def submit(self, tick: Tick) -> None:
        """
        Validate and submit a tick to the bounded queue.

        Queue.put() naturally applies back-pressure when the queue
        reaches its configured capacity.
        """
        if self._shutdown.is_set():
            raise RuntimeError(
                "Cannot submit tick after shutdown has started."
            )

        try:
            validate_tick(tick)
        except ValueError:
            self._ticks_rejected += 1
            raise

        await self._queue.put(tick)

    async def run(self) -> None:
        """
        Run the single consumer until the shutdown sentinel arrives.

        Only this task mutates the BarAggregator state.
        """
        while True:
            tick = await self._queue.get()

            try:
                if tick is None:
                    return

                bars = self._aggregator.process_tick(tick)

                self._ticks_processed += 1

                await self._publish_bars(bars)

            finally:
                self._queue.task_done()

    async def shutdown(self) -> None:
        """
        Gracefully stop the runtime.

        Existing queued ticks are processed before the shutdown
        sentinel is inserted.
        """
        if self._shutdown.is_set():
            if self._consumer_task is not None:
                await self._consumer_task

            return

        self._shutdown.set()

        # Wait until all previously submitted ticks are processed.
        await self._queue.join()

        if self._consumer_task is not None:
            await self._queue.put(None)

            await self._consumer_task

            self._consumer_task = None

    async def flush(self) -> None:
        """
        Flush remaining aggregation state into BarEvents.

        Wait for all already-submitted ticks to be consumed before
        accessing the stateful aggregator. This prevents a race
        between the consumer and flush().
        """
        if self._consumer_task is not None:
            await self._queue.join()

        bars = self._aggregator.flush()

        await self._publish_bars(bars)

    async def consume(
        self,
        stream: AsyncIterator[Tick],
    ) -> None:
        """
        Consume ticks from an asynchronous market-data stream.

        The runtime starts automatically and shuts down gracefully
        when the stream ends.
        """
        await self.start()

        try:
            async for tick in stream:
                await self.submit(tick)

        finally:
            await self.shutdown()

    async def _publish_bars(
        self,
        bars: list[Bar],
    ) -> None:
        """Publish finalized bars through the event bus."""
        for bar in bars:
            await self._event_bus.publish(
                BarEvent(
                    timestamp=bar.timestamp,
                    symbol=bar.symbol,
                    data=bar,
                )
            )

            self._bars_published += 1