from decimal import Decimal

from trading_system.core.models.market import Bar
from trading_system.indicators.snapshot import IndicatorSnapshot
from trading_system.regime.config import RegimeThresholds
from trading_system.regime.enums import MarketRegime, RegimeAction
from trading_system.regime.models import RegimeSnapshot
from trading_system.regime.scoring import RegimeScore


def classify_score(
    score: RegimeScore,
    thresholds: RegimeThresholds | None = None,
) -> RegimeSnapshot:
    thresholds = thresholds or RegimeThresholds()

    if score.risk_score >= thresholds.risk_off:
        return RegimeSnapshot(
            regime=MarketRegime.RISK_OFF,
            action=RegimeAction.BLOCK,
            volatility_multiplier=Decimal(1),
            position_multiplier=Decimal(0),
            grid_spacing_multiplier=Decimal(1),
            allow_new_entries=False,
            reason="Risk score exceeded the risk-off threshold.",
        )

    if score.volatility_score >= thresholds.high_volatility:
        return RegimeSnapshot(
            regime=MarketRegime.HIGH_VOLATILITY,
            action=RegimeAction.REDUCE,
            volatility_multiplier=Decimal("1.5"),
            position_multiplier=Decimal("0.5"),
            grid_spacing_multiplier=Decimal("1.5"),
            allow_new_entries=True,
            reason="Volatility exceeded the high-volatility threshold.",
        )

    if score.trend_score >= thresholds.strong_trend:
        return RegimeSnapshot(
            regime=MarketRegime.TRENDING,
            action=RegimeAction.ALLOW,
            volatility_multiplier=Decimal(1),
            position_multiplier=Decimal(1),
            grid_spacing_multiplier=Decimal("1.25"),
            allow_new_entries=True,
            reason="Trend strength exceeded the trending threshold.",
        )

    if score.volatility_score <= thresholds.low_volatility:
        return RegimeSnapshot(
            regime=MarketRegime.LOW_VOLATILITY,
            action=RegimeAction.ALLOW,
            volatility_multiplier=Decimal("0.75"),
            position_multiplier=Decimal(1),
            grid_spacing_multiplier=Decimal("0.75"),
            allow_new_entries=True,
            reason="Volatility is below the low-volatility threshold.",
        )

    return RegimeSnapshot(
        regime=MarketRegime.NORMAL,
        action=RegimeAction.ALLOW,
        volatility_multiplier=Decimal(1),
        position_multiplier=Decimal(1),
        grid_spacing_multiplier=Decimal(1),
        allow_new_entries=True,
        reason="No regime override triggered.",
    )

def classify_regime(
    bar: Bar,
    indicators: IndicatorSnapshot,
) -> RegimeSnapshot:
    """Classify a bar using indicator-derived market proxies."""

    # Preserve the warm-up behavior of the original regime engine.
    if indicators.atr is None:
        return RegimeSnapshot(
            regime=MarketRegime.NORMAL,
            action=RegimeAction.ALLOW,
            volatility_multiplier=Decimal(1),
            position_multiplier=Decimal(1),
            grid_spacing_multiplier=Decimal(1),
            allow_new_entries=True,
            reason="Indicator warm-up period.",
        )

    trend_strength = Decimal(0)

    if (
        indicators.ema_fast is not None
        and indicators.ema_slow is not None
    ):
        trend_strength = abs(
            indicators.ema_fast - indicators.ema_slow
        )

    score = RegimeScore(
        trend_score=trend_strength,
        volatility_score=Decimal(0),
        risk_score=Decimal(0),
    )

    return classify_score(score)

