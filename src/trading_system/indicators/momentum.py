from collections.abc import Sequence
from decimal import Decimal


def rsi(
    closes: Sequence[Decimal],
    period: int = 14,
) -> list[Decimal | None]:
    """
    Calculate Relative Strength Index using Wilder smoothing.
    """
    if period <= 0:
        raise ValueError("period must be positive.")

    if len(closes) <= period:
        return [None] * len(closes)

    result: list[Decimal | None] = [None] * len(closes)

    gains: list[Decimal] = []
    losses: list[Decimal] = []

    for index in range(1, len(closes)):
        change = closes[index] - closes[index - 1]

        gains.append(max(change, Decimal(0)))
        losses.append(max(-change, Decimal(0)))

    average_gain = (
        sum(gains[:period], Decimal(0))
        / Decimal(period)
    )

    average_loss = (
        sum(losses[:period], Decimal(0))
        / Decimal(period)
    )

    result[period] = _calculate_rsi(
        average_gain,
        average_loss,
    )

    for index in range(period + 1, len(closes)):
        average_gain = (
            (
                average_gain * Decimal(period - 1)
            )
            + gains[index - 1]
        ) / Decimal(period)

        average_loss = (
            (
                average_loss * Decimal(period - 1)
            )
            + losses[index - 1]
        ) / Decimal(period)

        result[index] = _calculate_rsi(
            average_gain,
            average_loss,
        )

    return result


def _calculate_rsi(
    average_gain: Decimal,
    average_loss: Decimal,
) -> Decimal:
    if average_loss == 0:
        return Decimal(100)

    relative_strength = average_gain / average_loss

    return Decimal(100) - (
        Decimal(100)
        / (Decimal(1) + relative_strength)
    )