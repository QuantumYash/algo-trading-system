from decimal import Decimal

from trading_system.core.models.fills import Fill
from trading_system.core.models.market import Bar
from trading_system.core.models.orders import OrderIntent
from trading_system.core.models.positions import Position
from trading_system.execution.fill_simulator import FillSimulator
from trading_system.execution.fills import create_fill
from trading_system.execution.manager import OrderManager
from trading_system.execution.pnl import total_pnl
from trading_system.execution.positions import PositionManager
from trading_system.risk.engine import RiskEngine
from trading_system.risk.models import RiskState


class ExecutionEngine:
    def __init__(
        self,
        risk_engine: RiskEngine,
        order_manager: OrderManager,
        position_manager: PositionManager,
        fill_simulator: FillSimulator,
    ) -> None:
        self._risk_engine = risk_engine
        self._order_manager = order_manager
        self._position_manager = position_manager
        self._fill_simulator = fill_simulator

    async def execute(
        self,
        intents: tuple[OrderIntent, ...],
        bars: dict[str, Bar],
        risk_state: RiskState | None = None,
    ) -> tuple[Fill, ...]:
        fills: list[Fill] = []

        symbols = sorted(
            {intent.symbol for intent in intents}
        )

        for symbol in symbols:
            position = self._position_manager.get_position(symbol)

            symbol_intents = tuple(
                intent
                for intent in intents
                if intent.symbol == symbol
            )

            decision = self._risk_engine.evaluate(
                intents=symbol_intents,
                position=position,
                risk_state=risk_state,
            )

            if not decision.approved:
                continue

            bar = bars.get(symbol)

            if bar is None:
                continue

            for intent in decision.intents:
                order = await self._order_manager.submit(intent)

                simulation = self._fill_simulator.simulate(
                    order=order,
                    bar=bar,
                )

                if simulation is None:
                    continue

                price, commission, taxes = simulation

                fill = create_fill(
                    order=order,
                    price=price,
                    commission=commission,
                    taxes=taxes,
                )

                order.filled_quantity += fill.quantity

                self._position_manager.apply_fill(fill)

                fills.append(fill)

        return tuple(fills)

    def get_position(self, symbol: str) -> Position:
        return self._position_manager.get_position(symbol)

    def get_pnl(
        self,
        symbol: str,
        mark_price: Decimal,
    ) -> Decimal:
        position = self.get_position(symbol)

        return total_pnl(
            position,
            mark_price,
        )