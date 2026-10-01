from datetime import UTC, datetime
from decimal import Decimal

from trading_system.core.enums import OrderStatus, OrderType, Side
from trading_system.core.models.market import Bar
from trading_system.core.models.orders import Order
from trading_system.execution.fill_simulator import (
    CostConfig,
    FillSimulator,
    SlippageConfig,
)


def make_bar(
    open_price: str,
    high: str,
    low: str,
    close: str,
) -> Bar:
    return Bar(
        symbol="NIFTY",
        timestamp=datetime(
            2026,
            1,
            1,
            10,
            0,
            tzinfo=UTC,
        ),
        open=Decimal(open_price),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(close),
        volume=100,
    )


def make_order(
    side: Side,
    order_type: OrderType,
    limit_price: Decimal | None = None,
) -> Order:
    return Order(
        order_id="ORDER-1",
        client_order_id="CLIENT-1",
        symbol="NIFTY",
        side=side,
        quantity=1,
        order_type=order_type,
        status=OrderStatus.OPEN,
        limit_price=limit_price,
    )


def test_market_buy_uses_bar_open() -> None:
    simulator = FillSimulator(
        slippage=SlippageConfig(
            basis_points=Decimal(0),
        ),
    )

    order = make_order(
        Side.BUY,
        OrderType.MARKET,
    )

    result = simulator.simulate(
        order,
        make_bar("25000", "25100", "24900", "25050"),
    )

    assert result is not None

    price, commission, taxes = result

    assert price == Decimal(25000)
    assert commission == Decimal(0)
    assert taxes == Decimal(0)


def test_buy_slippage_increases_execution_price() -> None:
    simulator = FillSimulator(
        slippage=SlippageConfig(
            basis_points=Decimal(1),
        ),
    )

    order = make_order(
        Side.BUY,
        OrderType.MARKET,
    )

    result = simulator.simulate(
        order,
        make_bar("25000", "25100", "24900", "25050"),
    )

    assert result is not None

    price, _, _ = result

    assert price == Decimal("25002.5")


def test_sell_slippage_decreases_execution_price() -> None:
    simulator = FillSimulator(
        slippage=SlippageConfig(
            basis_points=Decimal(1),
        ),
    )

    order = make_order(
        Side.SELL,
        OrderType.MARKET,
    )

    result = simulator.simulate(
        order,
        make_bar("25000", "25100", "24900", "25050"),
    )

    assert result is not None

    price, _, _ = result

    assert price == Decimal("24997.5")


def test_limit_buy_fills_when_bar_crosses_limit() -> None:
    simulator = FillSimulator()

    order = make_order(
        Side.BUY,
        OrderType.LIMIT,
        Decimal(24950),
    )

    result = simulator.simulate(
        order,
        make_bar("25000", "25050", "24920", "25010"),
    )

    assert result is not None

    price, _, _ = result

    assert price == Decimal(24950)


def test_limit_buy_does_not_fill_when_price_not_reached() -> None:
    simulator = FillSimulator()

    order = make_order(
        Side.BUY,
        OrderType.LIMIT,
        Decimal(24950),
    )

    result = simulator.simulate(
        order,
        make_bar("25000", "25050", "24980", "25010"),
    )

    assert result is None


def test_limit_sell_fills_when_bar_crosses_limit() -> None:
    simulator = FillSimulator()

    order = make_order(
        Side.SELL,
        OrderType.LIMIT,
        Decimal(25050),
    )

    result = simulator.simulate(
        order,
        make_bar("25000", "25100", "24980", "25080"),
    )

    assert result is not None

    price, _, _ = result

    assert price == Decimal(25050)


def test_transaction_costs_are_calculated() -> None:
    simulator = FillSimulator(
    slippage=SlippageConfig(
        basis_points=Decimal(0),
    ),
    costs=CostConfig(
        commission_per_order=Decimal(20),
        tax_rate=Decimal("0.001"),
    ),
)
    order = make_order(
        Side.BUY,
        OrderType.MARKET,
    )

    result = simulator.simulate(
        order,
        make_bar("25000", "25100", "24900", "25050"),
    )

    assert result is not None

    price, commission, taxes = result

    assert price == Decimal(25000)
    assert commission == Decimal(20)
    assert taxes == Decimal(25)