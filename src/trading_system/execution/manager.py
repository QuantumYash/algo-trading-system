
import asyncio
from datetime import UTC, datetime

from trading_system.core.enums import OrderStatus
from trading_system.core.models.orders import Order, OrderIntent
from trading_system.execution.broker.base import (
    BrokerAdapter,
    PermanentBrokerError,
    TransientBrokerError,
)
from trading_system.execution.idempotency import build_client_order_id
from trading_system.execution.models import RetryConfig
from trading_system.execution.rate_limiter import AsyncRateLimiter
from trading_system.execution.state_machine import validate_transition


class OrderManager:
    def __init__(
        self,
        broker: BrokerAdapter,
        rate_limiter: AsyncRateLimiter,
        retry_config: RetryConfig | None = None,
    ) -> None:
        self._broker = broker
        self._rate_limiter = rate_limiter
        self._retry_config = retry_config or RetryConfig()

        self._orders_by_client_id: dict[str, Order] = {}
        self._lock = asyncio.Lock()

    async def submit(self, intent: OrderIntent) -> Order:
        client_order_id = build_client_order_id(intent)

        # Idempotency check
        async with self._lock:
            existing = self._orders_by_client_id.get(client_order_id)

            if existing is not None:
                return existing

            order = Order(
                order_id="",
                client_order_id=client_order_id,
                symbol=intent.symbol,
                side=intent.side,
                quantity=intent.quantity,
                order_type=intent.order_type,
                limit_price=intent.limit_price,
                stop_price=intent.stop_price,
                status=OrderStatus.CREATED,
                created_at=datetime.now(UTC),
            )

            self._orders_by_client_id[client_order_id] = order

        return await self._submit_with_retry(intent, order)

    async def _submit_with_retry(
        self,
        intent: OrderIntent,
        order: Order,
    ) -> Order:
        attempts = self._retry_config.max_attempts

        for attempt in range(1, attempts + 1):
            try:
                await self._rate_limiter.acquire()

                validate_transition(
                    order.status,
                    OrderStatus.PENDING,
                )

                order.status = OrderStatus.PENDING

                submitted_order = await self._broker.submit_order(intent)

                submitted_order.client_order_id = order.client_order_id
                submitted_order.updated_at = datetime.now(UTC)

                return submitted_order

            except PermanentBrokerError:
                order.status = OrderStatus.REJECTED
                raise

            except TransientBrokerError:
                if attempt >= attempts:
                    order.status = OrderStatus.REJECTED
                    raise

                delay = min(
                    self._retry_config.base_delay_seconds * (2 ** (attempt - 1)),
                    self._retry_config.max_delay_seconds,
                )

                await asyncio.sleep(delay)

        raise RuntimeError("Order submission loop exited unexpectedly")