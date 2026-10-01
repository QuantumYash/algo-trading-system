from decimal import Decimal

from trading_system.core.enums import Side
from trading_system.core.models.fills import Fill
from trading_system.execution.positions import PositionManager


def make_fill(
    side: Side,
    quantity: int,
    price: str,
) -> Fill:
    return Fill(
        fill_id="F1",
        order_id="O1",
        symbol="NIFTY",
        side=side,
        quantity=quantity,
        price=Decimal(price),
        timestamp=None,  # type: ignore[arg-type]
    )


def test_buy_creates_long_position() -> None:
    manager = PositionManager()

    position = manager.apply_fill(
        make_fill(Side.BUY, 10, "100")
    )

    assert position.quantity == 10
    assert position.average_price == Decimal(100)