from decimal import Decimal

from trading_system.core.enums import OrderType, Side
from trading_system.core.models.positions import Position
from trading_system.indicators.snapshot import IndicatorSnapshot
from trading_system.regime.enums import MarketRegime, RegimeAction
from trading_system.regime.models import RegimeSnapshot
from trading_system.strategies.grid import GridConfig, GridStrategy
from trading_system.strategies.models import StrategyContext


def test_grid_disables_pyramiding() -> None:
    strategy = GridStrategy(
        GridConfig(
            max_levels=2,
            pyramid=False,
        )
    )

    decision = strategy.generate_decision(
        make_context(position_quantity=2)
    )

    assert decision.intents == ()
    assert "pyramiding" in decision.reason.lower()

def test_grid_disables_short_pyramiding() -> None:
    strategy = GridStrategy(
        GridConfig(
            max_levels=2,
            pyramid=False,
        )
    )

    decision = strategy.generate_decision(
        make_context(position_quantity=-2)
    )

    assert decision.intents == ()
    assert "pyramiding" in decision.reason.lower()

def test_grid_generates_initial_grid_when_flat_and_pyramiding_disabled() -> None:
    strategy = GridStrategy(
        GridConfig(
            max_levels=2,
            pyramid=False,
        )
    )

    decision = strategy.generate_decision(
        make_context(position_quantity=0)
    )

    assert len(decision.intents) == 4

def make_context(
    position_quantity: int = 0,
    atr: Decimal | None = Decimal(2),
    allow_entries: bool = True,
) -> StrategyContext:
    indicators = IndicatorSnapshot(
        ema_fast=Decimal(105),
        ema_slow=Decimal(100),
        rsi=Decimal(60),
        atr=atr,
        vwap=Decimal(102),
    )

    regime = RegimeSnapshot(
        regime=MarketRegime.NORMAL,
        action=RegimeAction.ALLOW,
        volatility_multiplier=Decimal(1),
        position_multiplier=Decimal(1),
        grid_spacing_multiplier=Decimal(1),
        allow_new_entries=allow_entries,
        reason="test",
    )

    return StrategyContext(
        symbol="TEST",
        price=Decimal(100),
        indicators=indicators,
        regime=regime,
        position=Position(
            symbol="TEST",
            quantity=position_quantity,
        ),
    )


def test_grid_generates_atr_spaced_levels() -> None:
    strategy = GridStrategy(
        GridConfig(
            quantity=2,
            atr_multiplier=Decimal("1.5"),
            max_levels=2,
        )
    )

    levels = strategy.generate_levels(make_context())

    assert len(levels) == 4

    assert levels[0].side == Side.BUY
    assert levels[0].price == Decimal(97)

    assert levels[1].side == Side.SELL
    assert levels[1].price == Decimal(103)

    assert levels[2].price == Decimal(94)
    assert levels[3].price == Decimal(106)


def test_flat_position_generates_both_sides() -> None:
    strategy = GridStrategy(
        GridConfig(max_levels=2)
    )

    decision = strategy.generate_decision(
        make_context(position_quantity=0)
    )

    assert len(decision.intents) == 4


def test_long_position_only_pyramids_long() -> None:
    strategy = GridStrategy(
        GridConfig(max_levels=2)
    )

    decision = strategy.generate_decision(
        make_context(position_quantity=2)
    )

    assert len(decision.intents) == 2
    assert all(intent.side == Side.BUY for intent in decision.intents)


def test_short_position_only_pyramids_short() -> None:
    strategy = GridStrategy(
        GridConfig(max_levels=2)
    )

    decision = strategy.generate_decision(
        make_context(position_quantity=-2)
    )

    assert len(decision.intents) == 2
    assert all(intent.side == Side.SELL for intent in decision.intents)


def test_grid_uses_limit_orders() -> None:
    strategy = GridStrategy(
        GridConfig(max_levels=1)
    )

    decision = strategy.generate_decision(make_context())

    assert len(decision.intents) == 2

    for intent in decision.intents:
        assert intent.order_type == OrderType.LIMIT
        assert intent.limit_price is not None


def test_grid_blocks_entries_when_regime_blocks() -> None:
    strategy = GridStrategy()

    decision = strategy.generate_decision(
        make_context(allow_entries=False)
    )

    assert decision.intents == ()
    assert "blocked" in decision.reason.lower()


def test_grid_waits_for_atr() -> None:
    strategy = GridStrategy()

    decision = strategy.generate_decision(
        make_context(atr=None)
    )

    assert decision.intents == ()
    assert "ATR" in decision.reason


def test_grid_config_rejects_invalid_quantity() -> None:
    try:
        GridConfig(quantity=0)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")


def test_grid_config_rejects_invalid_levels() -> None:
    try:
        GridConfig(max_levels=0)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")