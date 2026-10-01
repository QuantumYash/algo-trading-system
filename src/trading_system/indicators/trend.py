from collections.abc import Sequence
from decimal import Decimal


def ema(
    values: Sequence[Decimal],
    period: int,
) -> list[Decimal | None]:
    """
    Calculate Exponential Moving Average.

    The first EMA value is seeded using the simple
    moving average of the first `period` observations.
    """
    if period <= 0:
        raise ValueError("period must be positive.")

    if len(values) < period:
        return [None] * len(values)

    result: list[Decimal | None] = [None] * len(values)

    multiplier = Decimal(2) / Decimal(period + 1)

    initial_sum = sum(
        values[:period],
        Decimal(0),
    )

    previous = initial_sum / Decimal(period)

    result[period - 1] = previous

    for index in range(period, len(values)):
        current = values[index]

        previous = (
            (current - previous) * multiplier
        ) + previous

        result[index] = previous

    return result