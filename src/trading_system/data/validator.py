from trading_system.core.models.market import Tick


def validate_tick(tick: Tick) -> None:
    """Validate a normalized market-data tick."""

    if not tick.symbol:
        raise ValueError("Tick symbol cannot be empty.")

    if tick.price <= 0:
        raise ValueError("Tick price must be positive.")

    if tick.volume < 0:
        raise ValueError("Tick volume cannot be negative.")

    if tick.bid is not None and tick.bid <= 0:
        raise ValueError("Bid price must be positive.")

    if tick.ask is not None and tick.ask <= 0:
        raise ValueError("Ask price must be positive.")

    if tick.bid is not None and tick.ask is not None and tick.bid > tick.ask:
        raise ValueError("Bid price cannot exceed ask price.")
