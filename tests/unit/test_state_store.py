from decimal import Decimal

from trading_system.core.models.positions import Position
from trading_system.execution.state_store import StateStore


def test_missing_state_returns_empty(tmp_path) -> None:
    store = StateStore(
        tmp_path / "state.json",
    )

    assert store.load_positions() == ()


def test_positions_are_persisted_and_restored(tmp_path) -> None:
    store = StateStore(
        tmp_path / "state.json",
    )

    positions = (
        Position(
            symbol="NIFTY",
            quantity=2,
            average_price=Decimal("25000.50"),
            realized_pnl=Decimal("125.25"),
        ),
        Position(
            symbol="BANKNIFTY",
            quantity=-1,
            average_price=Decimal(52000),
            realized_pnl=Decimal("-50.50"),
        ),
    )

    store.save_positions(positions)

    restored = store.load_positions()

    assert restored == positions


def test_state_file_is_created(tmp_path) -> None:
    path = tmp_path / "state.json"

    store = StateStore(path)

    store.save_positions(
        (
            Position(
                symbol="NIFTY",
                quantity=1,
                average_price=Decimal(25000),
            ),
        )
    )

    assert path.exists()