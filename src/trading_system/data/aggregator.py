from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from trading_system.core.models.market import Bar, Tick


@dataclass(slots=True)
class _BarAccumulator:
    """Mutable state used while constructing one OHLCV bar."""

    symbol: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int

    def update(self, tick: Tick) -> None:
        """Update the current bar with a new tick."""
        self.high = max(self.high, tick.price)
        self.low = min(self.low, tick.price)
        self.close = tick.price
        self.volume += tick.volume

    def to_bar(self) -> Bar:
        """Convert accumulated state into an immutable Bar."""
        return Bar(
            symbol=self.symbol,
            timestamp=self.timestamp,
            open=self.open,
            high=self.high,
            low=self.low,
            close=self.close,
            volume=self.volume,
        )


class BarAggregator:
    """
    Convert ticks into time-based OHLCV bars.

    The aggregator supports out-of-order ticks through a watermark
    controlled by max_lateness.

    Only one runtime consumer should mutate this object at a time.
    """

    def __init__(
        self,
        interval: timedelta = timedelta(minutes=1),
        max_lateness: timedelta = timedelta(seconds=0),
    ) -> None:
        if interval <= timedelta(0):
            raise ValueError("interval must be positive.")

        if max_lateness < timedelta(0):
            raise ValueError("max_lateness cannot be negative.")

        self._interval = interval
        self._max_lateness = max_lateness

        self._bars: dict[
            tuple[str, datetime],
            _BarAccumulator,
        ] = {}

        self._max_seen_timestamp: dict[
            str,
            datetime,
        ] = {}

        self._finalized_buckets: dict[
            str,
            set[datetime],
        ] = {}

    @property
    def interval(self) -> timedelta:
        """Configured bar interval."""
        return self._interval

    @property
    def max_lateness(self) -> timedelta:
        """Maximum tolerated event lateness."""
        return self._max_lateness

    def process_tick(self, tick: Tick) -> list[Bar]:
        """
        Process one tick and return any bars that became final.
        """
        timestamp = self._ensure_timezone(tick.timestamp)

        normalized_tick = Tick(
            symbol=tick.symbol,
            timestamp=timestamp,
            price=tick.price,
            volume=tick.volume,
            bid=tick.bid,
            ask=tick.ask,
        )

        max_seen = self._max_seen_timestamp.get(tick.symbol)

        if max_seen is None or timestamp > max_seen:
            self._max_seen_timestamp[tick.symbol] = timestamp
            max_seen = timestamp

        bucket_start = self._bucket_start(timestamp)
        key = (tick.symbol, bucket_start)

        finalized = self._finalized_buckets.setdefault(
            tick.symbol,
            set(),
        )

        # A late tick cannot recreate a bar that has already
        # been finalized.
        if bucket_start in finalized:
            return []

        accumulator = self._bars.get(key)

        if accumulator is None:
            self._bars[key] = _BarAccumulator(
                symbol=tick.symbol,
                timestamp=bucket_start,
                open=normalized_tick.price,
                high=normalized_tick.price,
                low=normalized_tick.price,
                close=normalized_tick.price,
                volume=normalized_tick.volume,
            )
        else:
            accumulator.update(normalized_tick)

        watermark = max_seen - self._max_lateness

        return self._finalize_before(
            symbol=tick.symbol,
            watermark=watermark,
        )

    def flush(
        self,
        symbol: str | None = None,
    ) -> list[Bar]:
        """
        Finalize all currently accumulated bars.

        If symbol is provided, only that symbol is flushed.
        """
        bars_to_finalize: list[tuple[str, datetime]] = []

        for key in self._bars:
            key_symbol, _ = key

            if symbol is None or key_symbol == symbol:
                bars_to_finalize.append(key)

        bars_to_finalize.sort(
            key=lambda item: (item[0], item[1])
        )

        finalized_bars: list[Bar] = []

        for key in bars_to_finalize:
            accumulator = self._bars.pop(key)

            finalized_bars.append(
                accumulator.to_bar()
            )

            self._finalized_buckets.setdefault(
                accumulator.symbol,
                set(),
            ).add(accumulator.timestamp)

        return finalized_bars

    def _finalize_before(
        self,
        symbol: str,
        watermark: datetime,
    ) -> list[Bar]:
        """Finalize bars whose end time is behind the watermark."""
        keys_to_finalize = [
            key
            for key in self._bars
            if key[0] == symbol
            and key[1] + self._interval <= watermark
        ]

        keys_to_finalize.sort(
            key=lambda item: item[1]
        )

        finalized_bars: list[Bar] = []

        for key in keys_to_finalize:
            accumulator = self._bars.pop(key)

            finalized_bars.append(
                accumulator.to_bar()
            )

            self._finalized_buckets.setdefault(
                symbol,
                set(),
            ).add(accumulator.timestamp)

        return finalized_bars

    def _bucket_start(
        self,
        timestamp: datetime,
    ) -> datetime:
        """Return the beginning of the interval containing timestamp."""
        timestamp = self._ensure_timezone(timestamp)

        epoch = datetime(
            1970,
            1,
            1,
            tzinfo=UTC,
        )

        elapsed = timestamp - epoch
        bucket_number = elapsed // self._interval

        return epoch + bucket_number * self._interval

    @staticmethod
    def _ensure_timezone(
        timestamp: datetime,
    ) -> datetime:
        """Require timezone-aware timestamps and normalize to UTC."""
        if timestamp.tzinfo is None:
            raise ValueError(
                "Tick timestamp must be timezone-aware."
            )

        return timestamp.astimezone(UTC)