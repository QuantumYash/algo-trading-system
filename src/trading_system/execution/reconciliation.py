from dataclasses import dataclass

from trading_system.core.models.orders import Order
from trading_system.core.models.positions import Position


@dataclass(frozen=True, slots=True)
class ReconciliationResult:
    missing_local_orders: tuple[Order, ...]
    missing_broker_orders: tuple[Order, ...]
    position_mismatches: tuple[str, ...]
    reconciled: bool


class ReconciliationEngine:
    def compare_orders(
        self,
        local_orders: tuple[Order, ...],
        broker_orders: tuple[Order, ...],
    ) -> ReconciliationResult:
        local_by_id = {
            order.client_order_id: order
            for order in local_orders
        }

        broker_by_id = {
            order.client_order_id: order
            for order in broker_orders
        }

        missing_local = tuple(
            broker_order
            for client_id, broker_order in broker_by_id.items()
            if client_id not in local_by_id
        )

        missing_broker = tuple(
            local_order
            for client_id, local_order in local_by_id.items()
            if client_id not in broker_by_id
        )

        return ReconciliationResult(
            missing_local_orders=missing_local,
            missing_broker_orders=missing_broker,
            position_mismatches=(),
            reconciled=not missing_local and not missing_broker,
        )

    def compare_positions(
        self,
        local_positions: tuple[Position, ...],
        broker_positions: tuple[Position, ...],
    ) -> tuple[str, ...]:
        local_by_symbol = {
            position.symbol: position
            for position in local_positions
        }

        broker_by_symbol = {
            position.symbol: position
            for position in broker_positions
        }

        symbols = local_by_symbol.keys() | broker_by_symbol.keys()

        mismatches: list[str] = []

        for symbol in sorted(symbols):
            local_position = local_by_symbol.get(symbol)
            broker_position = broker_by_symbol.get(symbol)

            local_quantity = (
                local_position.quantity
                if local_position is not None
                else 0
            )

            broker_quantity = (
                broker_position.quantity
                if broker_position is not None
                else 0
            )

            if local_quantity != broker_quantity:
                mismatches.append(
                    f"{symbol}: local={local_quantity}, broker={broker_quantity}"
                )

        return tuple(mismatches)