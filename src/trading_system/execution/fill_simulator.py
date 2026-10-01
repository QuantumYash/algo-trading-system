from dataclasses import dataclass
from decimal import Decimal

from trading_system.core.enums import OrderType, Side
from trading_system.core.models.market import Bar
from trading_system.core.models.orders import Order


@dataclass(frozen=True, slots=True)
class SlippageConfig:
    basis_points: Decimal = Decimal("1.0")

    def __post_init__(self) -> None:
        if self.basis_points < 0:
            raise ValueError("Slippage cannot be negative.")


@dataclass(frozen=True, slots=True)
class CostConfig:
    commission_per_order: Decimal = Decimal(0)
    tax_rate: Decimal = Decimal(0)

    def __post_init__(self) -> None:
        if self.commission_per_order < 0:
            raise ValueError("Commission cannot be negative.")
        if self.tax_rate < 0:
            raise ValueError("Tax rate cannot be negative.")


class FillSimulator:
    def __init__(
        self,
        slippage: SlippageConfig | None = None,
        costs: CostConfig | None = None,
    ) -> None:
        self._slippage = slippage or SlippageConfig()
        self._costs = costs or CostConfig()

    def simulate(
        self,
        order: Order,
        bar: Bar,
    ) -> tuple[Decimal, Decimal, Decimal] | None:
        fill_price = self._determine_fill_price(order, bar)

        if fill_price is None:
            return None

        execution_price = fill_price

        if order.order_type == OrderType.MARKET:
            execution_price = self._apply_slippage(
                fill_price,
                order.side,
            )

        commission = self._costs.commission_per_order

        gross_value = execution_price * order.quantity
        taxes = gross_value * self._costs.tax_rate

        return (
            execution_price,
            commission,
            taxes,
        )

    def _determine_fill_price(
        self,
        order: Order,
        bar: Bar,
    ) -> Decimal | None:
        if order.order_type == OrderType.MARKET:
            return bar.open

        if order.order_type == OrderType.LIMIT:
            return self._limit_fill_price(order, bar)

        return None

    @staticmethod
    def _limit_fill_price(
        order: Order,
        bar: Bar,
    ) -> Decimal | None:
        if order.limit_price is None:
            return None

        limit_price = order.limit_price

        if order.side == Side.BUY:
            if bar.low <= limit_price:
                return limit_price
            return None

        if bar.high >= limit_price:
            return limit_price

        return None

    def _apply_slippage(
        self,
        price: Decimal,
        side: Side,
    ) -> Decimal:
        slippage_rate = self._slippage.basis_points / Decimal(10000)
        adjustment = price * slippage_rate

        if side == Side.BUY:
            return price + adjustment

        return price - adjustment