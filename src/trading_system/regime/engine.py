from collections.abc import Sequence

from trading_system.core.models.market import Bar
from trading_system.indicators.snapshot import IndicatorSnapshot
from trading_system.regime.models import RegimeSnapshot
from trading_system.regime.rules import classify_regime


class MacroRegimeEngine:
    """
    Converts market/indicator conditions into a regime snapshot.

    The strategy consumes the snapshot but does not contain
    regime-classification logic itself.
    """

    def evaluate(
        self,
        bar: Bar,
        indicators: IndicatorSnapshot,
    ) -> RegimeSnapshot:
        return classify_regime(bar, indicators)

    def evaluate_series(
        self,
        bars: Sequence[Bar],
        indicators: Sequence[IndicatorSnapshot],
    ) -> list[RegimeSnapshot]:
        if len(bars) != len(indicators):
            raise ValueError(
                "bars and indicators must have the same length."
            )

        return [
            self.evaluate(bar, snapshot)
            for bar, snapshot in zip(bars, indicators, strict=True)
        ]