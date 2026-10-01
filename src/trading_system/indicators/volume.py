from collections.abc import Sequence
from decimal import Decimal

from trading_system.core.models.market import Bar


def vwap(bars: Sequence[Bar]) -> list[Decimal | None]:
    result: list[Decimal | None] = []

    cumulative_value = Decimal(0)
    cumulative_volume = 0

    for bar in bars:
        if bar.volume <= 0:
            result.append(None)
            continue

        typical_price = (
            bar.high + bar.low + bar.close
        ) / Decimal(3)

        cumulative_value += typical_price * Decimal(bar.volume)
        cumulative_volume += bar.volume

        result.append(
            cumulative_value / Decimal(cumulative_volume)
        )

    return result