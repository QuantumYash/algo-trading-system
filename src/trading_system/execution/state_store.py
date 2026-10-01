import json
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path

from trading_system.core.models.positions import Position


class StateStore:
    def __init__(self, path: Path) -> None:
        self._path = path

    def save_positions(
        self,
        positions: tuple[Position, ...],
    ) -> None:
        payload = {
            "positions": [
                {
                    **asdict(position),
                    "average_price": str(position.average_price),
                    "realized_pnl": str(position.realized_pnl),
                }
                for position in positions
            ],
        }

        self._path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary_path = self._path.with_suffix(".tmp")

        temporary_path.write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )

        temporary_path.replace(self._path)

    def load_positions(self) -> tuple[Position, ...]:
        if not self._path.exists():
            return ()

        payload = json.loads(
            self._path.read_text(encoding="utf-8"),
        )

        positions: list[Position] = []

        for item in payload.get("positions", []):
            positions.append(
                Position(
                    symbol=item["symbol"],
                    quantity=int(item["quantity"]),
                    average_price=Decimal(item["average_price"]),
                    realized_pnl=Decimal(item["realized_pnl"]),
                )
            )

        return tuple(positions)