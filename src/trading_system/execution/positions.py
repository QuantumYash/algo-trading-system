from decimal import Decimal

from trading_system.core.enums import Side
from trading_system.core.models.fills import Fill
from trading_system.core.models.positions import Position


class PositionManager:
    def __init__(self) -> None:
        self._positions: dict[str, Position] = {}

    def get_position(self, symbol: str) -> Position:
        return self._positions.setdefault(
            symbol,
            Position(symbol=symbol),
        )

    def apply_fill(self, fill: Fill) -> Position:
        position = self.get_position(fill.symbol)

        signed_quantity = (
            fill.quantity
            if fill.side == Side.BUY
            else -fill.quantity
        )

        old_quantity = position.quantity
        new_quantity = old_quantity + signed_quantity

        if old_quantity == 0:
            position.average_price = fill.price

        elif old_quantity > 0 and signed_quantity > 0:
            position.average_price = (
                position.average_price * old_quantity
                + fill.price * signed_quantity
            ) / new_quantity

        elif old_quantity < 0 and signed_quantity < 0:
            old_abs = abs(old_quantity)
            new_abs = abs(new_quantity)

            position.average_price = (
                position.average_price * old_abs
                + fill.price * abs(signed_quantity)
            ) / new_abs

        else:
            closing_quantity = min(
                abs(old_quantity),
                abs(signed_quantity),
            )

            if old_quantity > 0:
                position.realized_pnl += (
                    fill.price - position.average_price
                ) * closing_quantity
            else:
                position.realized_pnl += (
                    position.average_price - fill.price
                ) * closing_quantity

            if new_quantity == 0:
                position.average_price = Decimal(0)

            elif (old_quantity > 0 and new_quantity < 0) or (
                old_quantity < 0 and new_quantity > 0
            ):
                position.average_price = fill.price

        position.quantity = new_quantity

        return position