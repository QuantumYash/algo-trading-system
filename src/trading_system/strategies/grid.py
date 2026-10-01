from dataclasses import dataclass, field
from decimal import Decimal

from trading_system.core.enums import OrderType, Side
from trading_system.core.models.orders import OrderIntent
from trading_system.strategies.models import (
    GridLevel,
    StrategyContext,
    StrategyDecision,
)


@dataclass(slots=True)
class GridState:
    """Runtime state maintained by the grid strategy."""

    active_levels: set[tuple[int, Side]] = field(default_factory=set)

    def is_active(self, level: GridLevel) -> bool:
        return (level.level, level.side) in self.active_levels

    def activate(self, level: GridLevel) -> None:
        self.active_levels.add((level.level, level.side))

    def deactivate(self, level: GridLevel) -> None:
        self.active_levels.discard((level.level, level.side))

    def clear(self) -> None:
        self.active_levels.clear()

@dataclass(frozen=True, slots=True)
class GridConfig:
    """Configuration for the ATR-based grid."""

    quantity: int = 1
    atr_multiplier: Decimal = Decimal("1.0")
    max_levels: int = 3
    pyramid: bool = True
    strategy_id: str = "grid"

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise ValueError("quantity must be positive.")

        if self.atr_multiplier <= 0:
            raise ValueError("atr_multiplier must be positive.")

        if self.max_levels <= 0:
            raise ValueError("max_levels must be positive.")


class GridStrategy:
    """
    ATR-spaced grid strategy.

    The strategy generates OrderIntent objects only.
    Execution is handled elsewhere.
    """

    def _allowed_side(
    self,
    context: StrategyContext,
    ) -> Side | None:
        if context.position.quantity > 0:
            return Side.BUY

        if context.position.quantity < 0:
            return Side.SELL

        return None

    def __init__(self, config: GridConfig | None = None) -> None:
        self._config = config or GridConfig()
        self._state = GridState()

    @property
    def state(self) -> GridState:
        return self._state

    @property
    def config(self) -> GridConfig:
        return self._config

    def generate_levels(
        self,
        context: StrategyContext,
    ) -> tuple[GridLevel, ...]:
        """Generate price levels around the current market price."""

        if context.indicators.atr is None:
            return ()

        spacing = (
            context.indicators.atr
            * self._config.atr_multiplier
            * context.regime.grid_spacing_multiplier
        )

        levels: list[GridLevel] = []

        for level in range(1, self._config.max_levels + 1):
            levels.append(
                GridLevel(
                    price=context.price - (spacing * Decimal(level)),
                    side=Side.BUY,
                    level=level,
                )
            )

            levels.append(
                GridLevel(
                    price=context.price + (spacing * Decimal(level)),
                    side=Side.SELL,
                    level=level,
                )
            )

        return tuple(levels)

    def generate_decision(
    self,
    context: StrategyContext,
        ) -> StrategyDecision:
        """
        Generate grid orders for the current market state.
        """

        if context.indicators.atr is None:
            return StrategyDecision(
                intents=(),
                reason="ATR is not ready.",
            )

        if not context.regime.allow_new_entries:
            return StrategyDecision(
                intents=(),
                reason="New entries blocked by market regime.",
            )

        # Generate the grid first.
        levels = self.generate_levels(context)

        # Existing position determines whether we continue
        # pyramiding in the same direction.
        allowed_side = self._allowed_side(context)

        if allowed_side is not None:
            if not self._config.pyramid:
                return StrategyDecision(
                    intents=(),
                    reason="Pyramiding disabled while position is open.",
                )

            levels = tuple(
                level
                for level in levels
                if level.side == allowed_side
            )

        intents: list[OrderIntent] = []

        for level in levels:
            intents.append(
                OrderIntent(
                    symbol=context.symbol,
                    side=level.side,
                    quantity=self._config.quantity,
                    order_type=OrderType.LIMIT,
                    limit_price=level.price,
                    strategy_id=self._config.strategy_id,
                    reason=f"GRID_LEVEL_{level.level}",
                )
            )

        return StrategyDecision(
            intents=tuple(intents),
            reason="Grid levels generated.",
        )