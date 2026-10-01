
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RetryConfig:
    max_attempts: int = 3
    base_delay_seconds: float = 0.25
    max_delay_seconds: float = 5.0

    def __post_init__(self) -> None:
        if self.max_attempts <= 0:
            raise ValueError("max_attempts must be positive.")

        if self.base_delay_seconds <= 0:
            raise ValueError("base_delay_seconds must be positive.")

        if self.max_delay_seconds < self.base_delay_seconds:
            raise ValueError(
                "max_delay_seconds cannot be smaller than base_delay_seconds."
            )