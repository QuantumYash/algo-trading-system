
from decimal import Decimal

from trading_system.core.enums import Side
from trading_system.core.models.orders import OrderIntent
from trading_system.core.models.positions import Position
from trading_system.risk.config import RiskConfig
from trading_system.risk.models import RiskDecision, RiskState


class RiskEngine:
    """Validate strategy orders against account-level risk limits."""

    def __init__(
        self,
        config: RiskConfig | None = None,
    ) -> None:
        self._config = config or RiskConfig()

    @property
    def config(self) -> RiskConfig:
        return self._config

    def evaluate(
        self,
        intents: tuple[OrderIntent, ...],
        position: Position,
        risk_state: RiskState | None = None,
    ) -> RiskDecision:
        """
        Evaluate a collection of strategy intents.

        No order is executed here. This method only approves or
        rejects the proposed intents.
        """

        state = risk_state or RiskState()

        if self._config.kill_switch or state.kill_switch:
            return self._blocked(
                reason="Kill switch is active.",
                position=position,
            )

        if state.daily_pnl <= -self._config.daily_loss_limit:
            return self._blocked(
                reason="Daily loss limit breached.",
                position=position,
            )

        if not intents:
            return RiskDecision(
                approved=True,
                intents=(),
                reason="No intents to evaluate.",
                projected_position=position.quantity,
                projected_notional=Decimal(0),
            )

        projected_quantity = position.quantity
        projected_notional = Decimal(0)
        approved_intents: list[OrderIntent] = []

        for intent in intents:
            if intent.quantity <= 0:
                return self._blocked(
                    reason="Order quantity must be positive.",
                    position=position,
                )

            if intent.quantity > self._config.max_order_quantity:
                return self._blocked(
                    reason=(
                        f"Order quantity {intent.quantity} exceeds "
                        f"maximum {self._config.max_order_quantity}."
                    ),
                    position=position,
                )

            signed_quantity = self._signed_quantity(intent)

            projected_quantity += signed_quantity

            if (
                abs(projected_quantity)
                > self._config.max_position_quantity
            ):
                return self._blocked(
                    reason=(
                        f"Projected position {projected_quantity} exceeds "
                        f"maximum {self._config.max_position_quantity}."
                    ),
                    position=position,
                )

            order_notional = self._order_notional(intent)

            projected_notional += order_notional

            if projected_notional > self._config.max_notional:
                return self._blocked(
                    reason=(
                        f"Projected notional {projected_notional} exceeds "
                        f"maximum {self._config.max_notional}."
                    ),
                    position=position,
                )

            approved_intents.append(intent)

        return RiskDecision(
            approved=True,
            intents=tuple(approved_intents),
            reason="All intents passed risk checks.",
            projected_position=projected_quantity,
            projected_notional=projected_notional,
        )

    def _blocked(
        self,
        reason: str,
        position: Position,
    ) -> RiskDecision:
        return RiskDecision(
            approved=False,
            intents=(),
            reason=reason,
            projected_position=position.quantity,
            projected_notional=Decimal(0),
        )

    @staticmethod
    def _signed_quantity(intent: OrderIntent) -> int:
        if intent.side == Side.BUY:
            return intent.quantity

        return -intent.quantity

    @staticmethod
    def _order_notional(intent: OrderIntent) -> Decimal:
        """
        Calculate order notional.

        Limit orders use their limit price. Market orders currently
        have zero notional because an execution price is not yet known.
        The Order Manager/Broker layer will apply the actual fill price.
        """
        if intent.limit_price is None:
            return Decimal(0)

        return intent.limit_price * Decimal(intent.quantity)