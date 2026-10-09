"""Shared sensor lifecycle, independent of robot-specific transports."""
import pytest

from ecosystem.sensor import GenericSensor


class CounterSensor(GenericSensor[int]):
    def __init__(self):
        self.opened = False
        self.count = 0

    async def initialize(self) -> None:
        self.opened = True

    async def read(self, timeout_s: float = 1.0) -> int:
        self._check_timeout(timeout_s)
        if not self.opened:
            raise RuntimeError("closed")
        self.count += 1
        return self.count

    async def close(self) -> None:
        self.opened = False


def test_lifecycle_methods_are_required():
    with pytest.raises(TypeError):
        GenericSensor()

    class MissingClose(GenericSensor[int]):
        async def initialize(self):
            pass

        async def read(self, timeout_s=1.0):
            return 0

    with pytest.raises(TypeError):
        MissingClose()


@pytest.mark.asyncio
async def test_persistent_reader_lifecycle():
    sensor = CounterSensor()
    await sensor.initialize()
    try:
        assert [await sensor.read() for _ in range(3)] == [1, 2, 3]
    finally:
        await sensor.close()
    assert not sensor.opened


@pytest.mark.asyncio
async def test_optional_context_manager_closes_on_exception():
    sensor = CounterSensor()
    with pytest.raises(ValueError, match="consumer failed"):
        async with sensor as entered:
            assert entered is sensor
            assert await entered.read() == 1
            raise ValueError("consumer failed")
    assert not sensor.opened


@pytest.mark.asyncio
async def test_timeout_validation_is_shared():
    async with CounterSensor() as sensor:
        for timeout in (0, -1, float("nan"), float("inf")):
            with pytest.raises(ValueError, match="finite and positive"):
                await sensor.read(timeout)
        assert await sensor.read(.01) == 1


def test_processed_imu_requires_complete_state_and_health_interface():
    from dataclasses import FrozenInstanceError
    from ecosystem.imu import Imu, ImuState

    class MissingHealth(Imu):
        async def initialize(self):
            pass

        async def read(self, timeout_s=1.0):
            pass

        async def close(self):
            pass

    with pytest.raises(TypeError):
        MissingHealth()
    with pytest.raises(TypeError):
        ImuState(timestamp_s=1, timestamp_clock="simulation")
    state = ImuState(1, "simulation", (1, 0, 0, 0), (0, 0, 0), (0, 0, 0),
                     (0, 0, 0), (0, 0, 0), (0, 0, 0))
    with pytest.raises(FrozenInstanceError):
        state.position_m = (1, 2, 3)
    assert state.acceleration_frame == "boot"
    assert not state.acceleration_includes_gravity
