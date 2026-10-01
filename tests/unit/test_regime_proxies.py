
from decimal import Decimal

import pytest

from trading_system.regime.proxies import MacroProxies


def test_macro_proxies_accept_valid_values() -> None:
    proxies = MacroProxies(
        volatility=Decimal("1.5"),
        trend_strength=Decimal("2.0"),
        market_return=Decimal("-0.02"),
        volume_ratio=Decimal("1.4"),
    )

    assert proxies.volatility == Decimal("1.5")
    assert proxies.market_return == Decimal("-0.02")


def test_negative_volatility_is_rejected() -> None:
    with pytest.raises(ValueError):
        MacroProxies(
            volatility=Decimal(-1),
        )


def test_negative_trend_strength_is_rejected() -> None:
    with pytest.raises(ValueError):
        MacroProxies(
            trend_strength=Decimal(-1),
        )


def test_negative_volume_ratio_is_rejected() -> None:
    with pytest.raises(ValueError):
        MacroProxies(
            volume_ratio=Decimal(-1),
        )


def test_negative_market_return_is_allowed() -> None:
    proxies = MacroProxies(
        market_return=Decimal("-0.03"),
    )

    assert proxies.market_return == Decimal("-0.03")