from collections.abc import Sequence
from decimal import Decimal

from trading_system.core.models.market import Bar


def true_range(
    bars: Sequence[Bar],
) -> list[Decimal]:
    """
    Calculate True Range for every bar.
    """
    if not bars:
        return []

    result: list[Decimal] = [
        bars[0].high - bars[0].low
    ]

    for index in range(1, len(bars)):
        current = bars[index]
        previous = bars[index - 1]

        range_high_low = (
            current.high - current.low
        )

        range_high_previous_close = abs(
            current.high - previous.close
        )

        range_low_previous_close = abs(
            current.low - previous.close
        )

        result.append(
            max(
                range_high_low,
                range_high_previous_close,
                range_low_previous_close,
            )
        )

    return result


def atr(
    bars: Sequence[Bar],
    period: int = 14,
) -> list[Decimal | None]:
    """
    Calculate Average True Range using Wilder smoothing.
    """
    if period <= 0:
        raise ValueError("period must be positive.")

    ranges = true_range(bars)

    if len(ranges) < period:
        return [None] * len(ranges)

    result: list[Decimal | None] = [None] * len(ranges)

    average = (
        sum(ranges[:period], Decimal(0))
        / Decimal(period)
    )

    result[period - 1] = average

    for index in range(period, len(ranges)):
        average = (
            (
                average * Decimal(period - 1)
            )
            + ranges[index]
        ) / Decimal(period)

        result[index] = average

    return result