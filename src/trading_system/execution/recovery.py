from dataclasses import dataclass

from trading_system.core.models.orders import Order
from trading_system.core.models.positions import Position
from trading_system.execution.reconciliation import (
    ReconciliationEngine,
    ReconciliationResult,
)
from trading_system.execution.state_store import StateStore


@dataclass(frozen=True, slots=True)
class RecoveryResult:
    ready_for_trading: bool
    reconciliation: ReconciliationResult
    local_positions: tuple[Position, ...]
    broker_positions: tuple[Position, ...]


class RecoveryManager:
    def __init__(
        self,
        state_store: StateStore,
        reconciliation_engine: ReconciliationEngine,
    ) -> None:
        self._state_store = state_store
        self._reconciliation_engine = reconciliation_engine

    def recover(
        self,
        local_orders: tuple[Order, ...],
        broker_orders: tuple[Order, ...],
        broker_positions: tuple[Position, ...],
    ) -> RecoveryResult:
        local_positions = self._state_store.load_positions()

        order_result = self._reconciliation_engine.compare_orders(
            local_orders=local_orders,
            broker_orders=broker_orders,
        )

        position_mismatches = self._reconciliation_engine.compare_positions(
            local_positions=local_positions,
            broker_positions=broker_positions,
        )

        reconciliation = ReconciliationResult(
            missing_local_orders=order_result.missing_local_orders,
            missing_broker_orders=order_result.missing_broker_orders,
            position_mismatches=position_mismatches,
            reconciled=(
                order_result.reconciled
                and not position_mismatches
            ),
        )

        return RecoveryResult(
            ready_for_trading=reconciliation.reconciled,
            reconciliation=reconciliation,
            local_positions=local_positions,
            broker_positions=broker_positions,
        )