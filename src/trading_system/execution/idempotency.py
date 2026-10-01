import hashlib

from trading_system.core.models.orders import OrderIntent


def build_client_order_id(intent: OrderIntent) -> str:
    """Create a deterministic ID for an order intent."""

    payload = "|".join(
        (
            intent.strategy_id,
            intent.symbol,
            intent.side.value,
            str(intent.quantity),
            intent.order_type.value,
            str(intent.limit_price),
            str(intent.stop_price),
            intent.reason,
        )
    )

    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()

    return f"TS-{digest[:20]}"