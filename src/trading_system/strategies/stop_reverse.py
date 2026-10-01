from dataclasses import dataclass
from decimal import Decimal

from trading_system.core.enums import OrderType, Side
from trading_system.core.models.orders import OrderIntent
from trading_system.strategies.models import StrategyContext, StrategyDecision


@dataclass(frozen=True, slots=True)
class StopReverseConfig:
    """Configuration for the stop-and-reverse strategy."""

    quantity: int = 1
    rsi_long_threshold: Decimal = Decimal(55)
    rsi_short_threshold: Decimal = Decimal(45)
    strategy_id: str = "stop_reverse"

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise ValueError("quantity must be positive.")

        if not 0 < self.rsi_short_threshold < self.rsi_long_threshold < 100:
            raise ValueError(
                "RSI thresholds must satisfy "
                "0 < short threshold < long threshold < 100."
            )


class StopReverseStrategy:
    """
    EMA-trend + RSI-confirmation stop-and-reverse strategy.

    The strategy produces OrderIntent objects only.
    It does not execute orders directly.
    """

    def __init__(
        self,
        config: StopReverseConfig | None = None,
    ) -> None:
        self._config = config or StopReverseConfig()

    @property
    def config(self) -> StopReverseConfig:
        return self._config

    def generate_decision(
        self,
        context: StrategyContext,
    ) -> StrategyDecision:
        """Generate a new position or reverse an existing position."""

        if not context.regime.allow_new_entries:
            return StrategyDecision(
                intents=(),
                reason="New entries blocked by market regime.",
            )

        indicators = context.indicators

        if indicators.ema_fast is None or indicators.ema_slow is None:
            return StrategyDecision(
                intents=(),
                reason="EMA indicators are not ready.",
            )

        if indicators.rsi is None:
            return StrategyDecision(
                intents=(),
                reason="RSI indicator is not ready.",
            )

        signal = self._signal(context)

        if signal is None:
            return StrategyDecision(
                intents=(),
                reason="No confirmed directional signal.",
            )

        current_quantity = context.position.quantity

        if current_quantity == 0:
            return StrategyDecision(
                intents=(self._entry_intent(context, signal),),
                reason=f"Opening {signal.value} position.",
            )

        current_side = (
            Side.BUY if current_quantity > 0 else Side.SELL
        )

        if current_side == signal:
            return StrategyDecision(
                intents=(),
                reason="Existing position already matches signal.",
            )

        return StrategyDecision(
            intents=self._reverse_intents(
                context=context,
                signal=signal,
            ),
            reason=f"Reversing position to {signal.value}.",
        )

    def _signal(self, context: StrategyContext) -> Side | None:
        indicators = context.indicators

        if (
            indicators.ema_fast is None
            or indicators.ema_slow is None
            or indicators.rsi is None
        ):
            return None

        bullish = (
            indicators.ema_fast > indicators.ema_slow
            and indicators.rsi >= self._config.rsi_long_threshold
        )

        bearish = (
            indicators.ema_fast < indicators.ema_slow
            and indicators.rsi <= self._config.rsi_short_threshold
        )

        if bullish:
            return Side.BUY

        if bearish:
            return Side.SELL

        return None

    def _entry_intent(
        self,
        context: StrategyContext,
        signal: Side,
    ) -> OrderIntent:
        return OrderIntent(
            symbol=context.symbol,
            side=signal,
            quantity=self._config.quantity,
            order_type=OrderType.MARKET,
            strategy_id=self._config.strategy_id,
            reason="STOP_REVERSE_ENTRY",
        )

    def _reverse_intents(
        self,
        context: StrategyContext,
        signal: Side,
    ) -> tuple[OrderIntent, ...]:
        current_quantity = abs(context.position.quantity)

        exit_side = (
            Side.SELL
            if context.position.quantity > 0
            else Side.BUY
        )

        exit_intent = OrderIntent(
            symbol=context.symbol,
            side=exit_side,
            quantity=current_quantity,
            order_type=OrderType.MARKET,
            strategy_id=self._config.strategy_id,
            reason="STOP_REVERSE_EXIT",
        )

        entry_intent = self._entry_intent(context, signal)

        return (exit_intent, entry_intent)