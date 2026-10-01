from collections.abc import Sequence

from trading_system.core.models.market import Bar
from trading_system.indicators.momentum import rsi
from trading_system.indicators.snapshot import IndicatorSnapshot
from trading_system.indicators.trend import ema
from trading_system.indicators.volatility import atr
from trading_system.indicators.volume import vwap


class IndicatorEngine:
    """Calculate all configured indicators over a sequence of bars."""

    def __init__(
        self,
        ema_fast_period: int = 12,
        ema_slow_period: int = 26,
        rsi_period: int = 14,
        atr_period: int = 14,
    ) -> None:
        if ema_fast_period <= 0:
            raise ValueError(
                "ema_fast_period must be positive."
            )

        if ema_slow_period <= 0:
            raise ValueError(
                "ema_slow_period must be positive."
            )

        if ema_fast_period >= ema_slow_period:
            raise ValueError(
                "ema_fast_period must be smaller "
                "than ema_slow_period."
            )

        if rsi_period <= 0:
            raise ValueError(
                "rsi_period must be positive."
            )

        if atr_period <= 0:
            raise ValueError(
                "atr_period must be positive."
            )

        self._ema_fast_period = ema_fast_period
        self._ema_slow_period = ema_slow_period
        self._rsi_period = rsi_period
        self._atr_period = atr_period

    def calculate(
        self,
        bars: Sequence[Bar],
    ) -> list[IndicatorSnapshot]:
        closes = [bar.close for bar in bars]

        ema_fast_values = ema(
            closes,
            self._ema_fast_period,
        )

        ema_slow_values = ema(
            closes,
            self._ema_slow_period,
        )

        rsi_values = rsi(
            closes,
            self._rsi_period,
        )

        atr_values = atr(
            bars,
            self._atr_period,
        )

        vwap_values = vwap(bars)

        snapshots: list[IndicatorSnapshot] = []

        for index in range(len(bars)):
            snapshots.append(
                IndicatorSnapshot(
                    ema_fast=ema_fast_values[index],
                    ema_slow=ema_slow_values[index],
                    rsi=rsi_values[index],
                    atr=atr_values[index],
                    vwap=vwap_values[index],
                )
            )

        return snapshots

    def latest(
        self,
        bars: Sequence[Bar],
    ) -> IndicatorSnapshot:
        if not bars:
            raise ValueError(
                "Cannot calculate indicators without bars."
            )

        return self.calculate(bars)[-1]