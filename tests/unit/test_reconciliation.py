from decimal import Decimal

from trading_system.core.enums import OrderStatus, OrderType, Side
from trading_system.core.models.orders import Order
from trading_system.core.models.positions import Position
from trading_system.execution.reconciliation import ReconciliationEngine


def make_order(
    client_order_id: str,
    symbol: str = "NIFTY",
) -> Order:
    return Order(
        order_id=f"ORDER-{client_order_id}",
        client_order_id=client_order_id,
        symbol=symbol,
        side=Side.BUY,
        quantity=1,
        order_type=OrderType.MARKET,
        status=OrderStatus.OPEN,
    )


def test_orders_reconcile_when_identical() -> None:
    engine = ReconciliationEngine()

    order = make_order("TS-001")

    result = engine.compare_orders(
        local_orders=(order,),
        broker_orders=(order,),
    )

    assert result.reconciled
    assert result.missing_local_orders == ()
    assert result.missing_broker_orders == ()


def test_detects_broker_order_missing_locally() -> None:
    engine = ReconciliationEngine()

    broker_order = make_order("TS-001")

    result = engine.compare_orders(
        local_orders=(),
        broker_orders=(broker_order,),
    )

    assert not result.reconciled
    assert result.missing_local_orders == (broker_order,)
    assert result.missing_broker_orders == ()


def test_detects_local_order_missing_at_broker() -> None:
    engine = ReconciliationEngine()

    local_order = make_order("TS-001")

    result = engine.compare_orders(
        local_orders=(local_order,),
        broker_orders=(),
    )

    assert not result.reconciled
    assert result.missing_local_orders == ()
    assert result.missing_broker_orders == (local_order,)


def test_positions_reconcile() -> None:
    engine = ReconciliationEngine()

    local = Position(
        symbol="NIFTY",
        quantity=2,
        average_price=Decimal(25000),
    )

    broker = Position(
        symbol="NIFTY",
        quantity=2,
        average_price=Decimal(25000),
    )

    mismatches = engine.compare_positions(
        local_positions=(local,),
        broker_positions=(broker,),
    )

    assert mismatches == ()


def test_detects_position_mismatch() -> None:
    engine = ReconciliationEngine()

    local = Position(
        symbol="NIFTY",
        quantity=2,
    )

    broker = Position(
        symbol="NIFTY",
        quantity=5,
    )

    mismatches = engine.compare_positions(
        local_positions=(local,),
        broker_positions=(broker,),
    )

    assert mismatches == (
        "NIFTY: local=2, broker=5",
    )