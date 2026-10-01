from decimal import Decimal

from trading_system.core.enums import OrderType, Side
from trading_system.core.models.positions import Position
from trading_system.indicators.snapshot import IndicatorSnapshot
from trading_system.regime.enums import MarketRegime, RegimeAction
from trading_system.regime.models import RegimeSnapshot
from trading_system.strategies.models import StrategyContext
from trading_system.strategies.stop_reverse import (
    StopReverseConfig,
    StopReverseStrategy,
)


def test_rsi_long_threshold_is_inclusive() -> None:
    strategy = StopReverseStrategy(
        StopReverseConfig(
            rsi_long_threshold=Decimal(55),
            rsi_short_threshold=Decimal(45),
        )
    )

    decision = strategy.generate_decision(
        make_context(
            ema_fast=Decimal(105),
            ema_slow=Decimal(100),
            rsi=Decimal(55),
        )
    )

    assert len(decision.intents) == 1
    assert decision.intents[0].side == Side.BUY

def test_rsi_short_threshold_is_inclusive() -> None:
    strategy = StopReverseStrategy(
        StopReverseConfig(
            rsi_long_threshold=Decimal(55),
            rsi_short_threshold=Decimal(45),
        )
    )

    decision = strategy.generate_decision(
        make_context(
            ema_fast=Decimal(95),
            ema_slow=Decimal(100),
            rsi=Decimal(45),
        )
    )

    assert len(decision.intents) == 1
    assert decision.intents[0].side == Side.SELL

def test_ema_bullish_but_rsi_not_confirmed_does_not_trade() -> None:
    strategy = StopReverseStrategy()

    decision = strategy.generate_decision(
        make_context(
            ema_fast=Decimal(105),
            ema_slow=Decimal(100),
            rsi=Decimal(50),
        )
    )

    assert decision.intents == ()

def test_ema_bearish_but_rsi_not_confirmed_does_not_trade() -> None:
    strategy = StopReverseStrategy()

    decision = strategy.generate_decision(
        make_context(
            ema_fast=Decimal(95),
            ema_slow=Decimal(100),
            rsi=Decimal(50),
        )
    )

    assert decision.intents == ()

def test_invalid_rsi_thresholds_are_rejected() -> None:
    try:
        StopReverseConfig(
            rsi_short_threshold=Decimal(60),
            rsi_long_threshold=Decimal(50),
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")

def test_rsi_threshold_above_100_is_rejected() -> None:
    try:
        StopReverseConfig(
            rsi_long_threshold=Decimal(100),
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")

def make_context(
    position_quantity: int = 0,
    ema_fast: Decimal | None = Decimal(105),
    ema_slow: Decimal | None = Decimal(100),
    rsi: Decimal | None = Decimal(60),
    allow_entries: bool = True,
) -> StrategyContext:
    indicators = IndicatorSnapshot(
        ema_fast=ema_fast,
        ema_slow=ema_slow,
        rsi=rsi,
        atr=Decimal(2),
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


def test_flat_bullish_signal_opens_long() -> None:
    strategy = StopReverseStrategy()

    decision = strategy.generate_decision(
        make_context(
            ema_fast=Decimal(105),
            ema_slow=Decimal(100),
            rsi=Decimal(60),
        )
    )

    assert len(decision.intents) == 1

    intent = decision.intents[0]

    assert intent.side == Side.BUY
    assert intent.quantity == 1
    assert intent.order_type == OrderType.MARKET
    assert intent.reason == "STOP_REVERSE_ENTRY"


def test_flat_bearish_signal_opens_short() -> None:
    strategy = StopReverseStrategy()

    decision = strategy.generate_decision(
        make_context(
            ema_fast=Decimal(95),
            ema_slow=Decimal(100),
            rsi=Decimal(40),
        )
    )

    assert len(decision.intents) == 1

    intent = decision.intents[0]

    assert intent.side == Side.SELL
    assert intent.quantity == 1


def test_long_position_reverses_to_short() -> None:
    strategy = StopReverseStrategy()

    decision = strategy.generate_decision(
        make_context(
            position_quantity=2,
            ema_fast=Decimal(95),
            ema_slow=Decimal(100),
            rsi=Decimal(40),
        )
    )

    assert len(decision.intents) == 2

    exit_intent, entry_intent = decision.intents

    assert exit_intent.side == Side.SELL
    assert exit_intent.quantity == 2
    assert exit_intent.reason == "STOP_REVERSE_EXIT"

    assert entry_intent.side == Side.SELL
    assert entry_intent.quantity == 1
    assert entry_intent.reason == "STOP_REVERSE_ENTRY"


def test_short_position_reverses_to_long() -> None:
    strategy = StopReverseStrategy()

    decision = strategy.generate_decision(
        make_context(
            position_quantity=-2,
            ema_fast=Decimal(105),
            ema_slow=Decimal(100),
            rsi=Decimal(60),
        )
    )

    assert len(decision.intents) == 2

    exit_intent, entry_intent = decision.intents

    assert exit_intent.side == Side.BUY
    assert exit_intent.quantity == 2

    assert entry_intent.side == Side.BUY
    assert entry_intent.quantity == 1


def test_existing_long_position_does_not_duplicate_long_entry() -> None:
    strategy = StopReverseStrategy()

    decision = strategy.generate_decision(
        make_context(
            position_quantity=2,
            ema_fast=Decimal(105),
            ema_slow=Decimal(100),
            rsi=Decimal(60),
        )
    )

    assert decision.intents == ()
    assert "already matches" in decision.reason


def test_existing_short_position_does_not_duplicate_short_entry() -> None:
    strategy = StopReverseStrategy()

    decision = strategy.generate_decision(
        make_context(
            position_quantity=-2,
            ema_fast=Decimal(95),
            ema_slow=Decimal(100),
            rsi=Decimal(40),
        )
    )

    assert decision.intents == ()
    assert "already matches" in decision.reason


def test_no_signal_does_not_trade() -> None:
    strategy = StopReverseStrategy()

    decision = strategy.generate_decision(
        make_context(
            ema_fast=Decimal(101),
            ema_slow=Decimal(100),
            rsi=Decimal(50),
        )
    )

    assert decision.intents == ()


def test_blocks_when_regime_blocks_entries() -> None:
    strategy = StopReverseStrategy()

    decision = strategy.generate_decision(
        make_context(allow_entries=False)
    )

    assert decision.intents == ()
    assert "blocked" in decision.reason.lower()


def test_waits_for_ema() -> None:
    strategy = StopReverseStrategy()

    decision = strategy.generate_decision(
        make_context(ema_fast=None)
    )

    assert decision.intents == ()
    assert "EMA" in decision.reason


def test_waits_for_rsi() -> None:
    strategy = StopReverseStrategy()

    decision = strategy.generate_decision(
        make_context(rsi=None)
    )

    assert decision.intents == ()
    assert "RSI" in decision.reason


def test_invalid_quantity_is_rejected() -> None:
    try:
        StopReverseConfig(quantity=0)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")