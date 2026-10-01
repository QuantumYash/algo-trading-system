from decimal import Decimal

from trading_system.core.models.market import Tick


def normalize_tick(
    symbol: str,
    timestamp,
    price,
    volume: int = 0,
    bid=None,
    ask=None,
) -> Tick:
    """
    Convert raw provider values into the internal Tick model.
    """

    return Tick(
        symbol=symbol,
        timestamp=timestamp,
        price=Decimal(str(price)),
        volume=int(volume),
        bid=Decimal(str(bid)) if bid is not None else None,
        ask=Decimal(str(ask)) if ask is not None else None,
    )
