"""Typed async sensor lifecycle for persistent, caller-owned readers."""
from __future__ import annotations

import math
from abc import ABC, abstractmethod
from typing import Generic, TypeVar


ReadT = TypeVar("ReadT")


class GenericSensor(ABC, Generic[ReadT]):
    """Initialize once, then await read() in a loop on the same event loop.

    Sensors own their transport resources. The caller controls polling and
    shutdown; using an async context manager is optional.
    """

    @abstractmethod
    async def initialize(self) -> None:
        """Open the sensor's transport resources."""

    @abstractmethod
    async def read(self, timeout_s: float = 1.0) -> ReadT:
        """Read a sample, raising TimeoutError if none arrives in time."""

    @abstractmethod
    async def close(self) -> None:
        """Release this sensor's transport resources."""

    async def __aenter__(self) -> GenericSensor[ReadT]:
        await self.initialize()
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    @staticmethod
    def _check_timeout(timeout_s: float) -> None:
        if not math.isfinite(timeout_s) or timeout_s <= 0:
            raise ValueError("timeout_s must be finite and positive")
