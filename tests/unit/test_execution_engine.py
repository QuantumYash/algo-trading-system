from datetime import UTC, datetime
from decimal import Decimal

import pytest

from trading_system.core.enums import OrderType, Side
from trading_system.core.models.market import Bar
from trading_system.core.models.orders import OrderIntent
from trading_system.execution.broker.paper import PaperBroker
from trading_system.execution.engine import ExecutionEngine
from trading_system.execution.fill_simulator import FillSimulator
from trading_system.execution.manager import OrderManager
from trading_system.execution.positions import PositionManager
from trading_system.execution.rate_limiter import AsyncRateLimiter
from trading_system.risk.config import RiskConfig
from trading_system.risk.engine import RiskEngine


@pytest.mark.asyncio
async def test_buy_order_flows_to_position() -> None:
    broker = PaperBroker()

    order_manager = OrderManager(
        broker=broker,
        rate_limiter=AsyncRateLimiter(
            max_calls=10,
            period_seconds=1,
        ),
    )

    position_manager = PositionManager()

    execution = ExecutionEngine(
        risk_engine=RiskEngine(
            RiskConfig(
                max_position_quantity=10,
                max_order_quantity=5,
            ),
        ),
        order_manager=order_manager,
        position_manager=position_manager,
        fill_simulator=FillSimulator()
    )

    intent = OrderIntent(
        symbol="NIFTY",
        side=Side.BUY,
        quantity=2,
        order_type=OrderType.MARKET,
        strategy_id="test",
        reason="TEST_ENTRY",
    )

    bar = Bar(
    symbol="NIFTY",
    timestamp=datetime.now(UTC),
    open=Decimal(25000),
    high=Decimal(25100),
    low=Decimal(24900),
    close=Decimal(25050),
    volume=1000,
    )

    fills = await execution.execute(
        intents=(intent,),
        bars={
            "NIFTY": bar,
        },
    )

    assert len(fills) == 1

    assert fills[0].price == Decimal("25002.5")

    position = execution.get_position("NIFTY")

    assert position.quantity == 2
    assert position.average_price == Decimal("25002.5")