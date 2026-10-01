from decimal import Decimal

import pytest

from trading_system.backtest.models import BacktestConfig


def test_backtest_config_accepts_valid_values() -> None:
    config = BacktestConfig(
        initial_capital=Decimal(100000),
        slippage_basis_points=Decimal("1.0"),
        commission_per_order=Decimal(20),
        tax_rate=Decimal("0.001"),
    )

    assert config.initial_capital == Decimal(100000)
    assert config.slippage_basis_points == Decimal("1.0")
    assert config.commission_per_order == Decimal(20)
    assert config.tax_rate == Decimal("0.001")


@pytest.mark.parametrize(
    "kwargs",
    [
        {"initial_capital": Decimal(0)},
        {"initial_capital": Decimal(-1)},
        {"slippage_basis_points": Decimal(-1)},
        {"commission_per_order": Decimal(-1)},
        {"tax_rate": Decimal(-1)},
    ],
)
def test_backtest_config_rejects_invalid_values(
    kwargs: dict[str, Decimal],
) -> None:
    with pytest.raises(ValueError):
        BacktestConfig(**kwargs)