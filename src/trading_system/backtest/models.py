from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from trading_system.core.models.market import Bar


@dataclass(frozen=True, slots=True)
class BacktestConfig:
    initial_capital: Decimal = Decimal(100000)
    slippage_basis_points: Decimal = Decimal("1.0")
    commission_per_order: Decimal = Decimal(0)
    tax_rate: Decimal = Decimal(0)

    def __post_init__(self) -> None:
        if self.initial_capital <= 0:
            raise ValueError("Initial capital must be positive.")

        if self.slippage_basis_points < 0:
            raise ValueError("Slippage cannot be negative.")

        if self.commission_per_order < 0:
            raise ValueError("Commission cannot be negative.")

        if self.tax_rate < 0:
            raise ValueError("Tax rate cannot be negative.")


@dataclass(frozen=True, slots=True)
class BacktestResult:
    initial_capital: Decimal
    final_equity: Decimal
    total_pnl: Decimal
    total_trades: int
    start_time: datetime | None
    end_time: datetime | None


@dataclass(frozen=True, slots=True)
class BacktestBar:
    bar: Bar