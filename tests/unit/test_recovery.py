from decimal import Decimal

from trading_system.core.enums import OrderStatus, OrderType, Side
from trading_system.core.models.orders import Order
from trading_system.core.models.positions import Position
from trading_system.execution.reconciliation import ReconciliationEngine
from trading_system.execution.recovery import RecoveryManager
from trading_system.execution.state_store import StateStore


def make_order(client_order_id: str) -> Order:
    return Order(
        order_id=f"ORDER-{client_order_id}",
        client_order_id=client_order_id,
        symbol="NIFTY",
        side=Side.BUY,
        quantity=1,
        order_type=OrderType.MARKET,
        status=OrderStatus.OPEN,
    )


def test_recovery_allows_trading_when_state_matches(tmp_path) -> None:
    store = StateStore(tmp_path / "state.json")

    position = Position(
        symbol="NIFTY",
        quantity=2,
        average_price=Decimal(25000),
    )

    store.save_positions((position,))

    order = make_order("TS-001")

    manager = RecoveryManager(
        state_store=store,
        reconciliation_engine=ReconciliationEngine(),
    )

    result = manager.recover(
        local_orders=(order,),
        broker_orders=(order,),
        broker_positions=(position,),
    )

    assert result.ready_for_trading
    assert result.reconciliation.reconciled
    assert result.reconciliation.position_mismatches == ()


def test_recovery_blocks_trading_on_position_mismatch(tmp_path) -> None:
    store = StateStore(tmp_path / "state.json")

    local_position = Position(
        symbol="NIFTY",
        quantity=2,
        average_price=Decimal(25000),
    )

    broker_position = Position(
        symbol="NIFTY",
        quantity=5,
        average_price=Decimal(25000),
    )

    store.save_positions((local_position,))

    manager = RecoveryManager(
        state_store=store,
        reconciliation_engine=ReconciliationEngine(),
    )

    result = manager.recover(
        local_orders=(),
        broker_orders=(),
        broker_positions=(broker_position,),
    )

    assert not result.ready_for_trading
    assert not result.reconciliation.reconciled
    assert result.reconciliation.position_mismatches == (
        "NIFTY: local=2, broker=5",
    )


def test_recovery_blocks_trading_on_order_mismatch(tmp_path) -> None:
    store = StateStore(tmp_path / "state.json")

    local_order = make_order("TS-001")

    store.save_positions(())

    manager = RecoveryManager(
        state_store=store,
        reconciliation_engine=ReconciliationEngine(),
    )

    result = manager.recover(
        local_orders=(local_order,),
        broker_orders=(),
        broker_positions=(),
    )

    assert not result.ready_for_trading
    assert not result.reconciliation.reconciled
    assert result.reconciliation.missing_broker_orders == (
        local_order,
    )