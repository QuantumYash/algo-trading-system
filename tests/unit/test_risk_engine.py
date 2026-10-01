
from decimal import Decimal

import pytest

from trading_system.core.enums import OrderType, Side
from trading_system.core.models.orders import OrderIntent
from trading_system.core.models.positions import Position
from trading_system.risk.config import RiskConfig
from trading_system.risk.engine import RiskEngine
from trading_system.risk.models import RiskState


def make_position(quantity: int = 0) -> Position:
    return Position(
        symbol="TEST",
        quantity=quantity,
    )


def make_limit_intent(
    side: Side = Side.BUY,
    quantity: int = 1,
    price: Decimal = Decimal(100),
) -> OrderIntent:
    return OrderIntent(
        symbol="TEST",
        side=side,
        quantity=quantity,
        order_type=OrderType.LIMIT,
        limit_price=price,
        strategy_id="test",
    )


def test_allows_valid_order() -> None:
    engine = RiskEngine()

    decision = engine.evaluate(
        intents=(make_limit_intent(quantity=2),),
        position=make_position(),
    )

    assert decision.approved is True
    assert len(decision.intents) == 1
    assert decision.projected_position == 2
    assert decision.projected_notional == Decimal(200)


def test_rejects_order_above_quantity_limit() -> None:
    engine = RiskEngine(
        RiskConfig(max_order_quantity=2),
    )

    decision = engine.evaluate(
        intents=(make_limit_intent(quantity=3),),
        position=make_position(),
    )

    assert decision.approved is False
    assert decision.intents == ()
    assert "quantity" in decision.reason.lower()


def test_rejects_position_limit() -> None:
    engine = RiskEngine(
        RiskConfig(max_position_quantity=5),
    )

    decision = engine.evaluate(
        intents=(make_limit_intent(quantity=2),),
        position=make_position(quantity=4),
    )

    assert decision.approved is False
    assert "position" in decision.reason.lower()


def test_sell_reduces_projected_position() -> None:
    engine = RiskEngine()

    decision = engine.evaluate(
        intents=(
            make_limit_intent(
                side=Side.SELL,
                quantity=2,
            ),
        ),
        position=make_position(quantity=5),
    )

    assert decision.approved is True
    assert decision.projected_position == 3


def test_rejects_notional_limit() -> None:
    engine = RiskEngine(
        RiskConfig(
            max_order_quantity=10,
            max_notional=Decimal(500)),
    )

    decision = engine.evaluate(
        intents=(make_limit_intent(quantity=6),),
        position=make_position(),
    )

    assert decision.approved is False
    assert "notional" in decision.reason.lower()


def test_kill_switch_blocks_orders() -> None:
    engine = RiskEngine(
        RiskConfig(kill_switch=True),
    )

    decision = engine.evaluate(
        intents=(make_limit_intent(),),
        position=make_position(),
    )

    assert decision.approved is False
    assert decision.intents == ()
    assert "kill switch" in decision.reason.lower()


def test_runtime_kill_switch_blocks_orders() -> None:
    engine = RiskEngine()

    decision = engine.evaluate(
        intents=(make_limit_intent(),),
        position=make_position(),
        risk_state=RiskState(kill_switch=True),
    )

    assert decision.approved is False


def test_daily_loss_limit_blocks_orders() -> None:
    engine = RiskEngine(
        RiskConfig(daily_loss_limit=Decimal(500)),
    )

    decision = engine.evaluate(
        intents=(make_limit_intent(),),
        position=make_position(),
        risk_state=RiskState(daily_pnl=Decimal(-500)),
    )

    assert decision.approved is False
    assert "daily loss" in decision.reason.lower()


def test_empty_intents_are_allowed() -> None:
    engine = RiskEngine()

    decision = engine.evaluate(
        intents=(),
        position=make_position(quantity=3),
    )

    assert decision.approved is True
    assert decision.intents == ()
    assert decision.projected_position == 3


def test_market_order_has_no_known_notional() -> None:
    engine = RiskEngine()

    intent = OrderIntent(
        symbol="TEST",
        side=Side.BUY,
        quantity=2,
        order_type=OrderType.MARKET,
    )

    decision = engine.evaluate(
        intents=(intent,),
        position=make_position(),
    )

    assert decision.approved is True
    assert decision.projected_notional == Decimal(0)


def test_invalid_configuration() -> None:
    with pytest.raises(ValueError):
        RiskConfig(max_position_quantity=0)

    with pytest.raises(ValueError):
        RiskConfig(max_order_quantity=0)

    with pytest.raises(ValueError):
        RiskConfig(max_notional=Decimal(0))

    with pytest.raises(ValueError):
        RiskConfig(daily_loss_limit=Decimal(0))