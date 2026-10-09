"""Portable contract for a module that produces processed inertial state."""
from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from enum import IntEnum
from typing import ClassVar, Literal

from .sensor import GenericSensor

Vector3 = tuple[float, float, float]
Quaternion = tuple[float, float, float, float]
Clock = Literal["device_uptime", "simulation"]


class ImuPhase(IntEnum):
    INITIALIZING = 0
    CALIBRATING = 1
    RUNNING = 2
    NO_SENSORS = 3


@dataclass(frozen=True, slots=True)
class ImuState:
    """Complete processed state in SI units; never raw accelerometer data.

    Orientation (w, x, y, z) rotates body vectors into the boot frame.
    Position is relative to the boot origin. Linear quantities use that fixed
    frame, acceleration excludes gravity, and angular quantities use body axes.
    Timestamps belong to the source clock (device uptime wraps after 2**32 ms),
    not wall time. Simulation time can reset when a world restarts.
    """

    timestamp_s: float
    timestamp_clock: Clock
    orientation_wxyz: Quaternion
    position_m: Vector3
    velocity_m_s: Vector3
    acceleration_m_s2: Vector3
    angular_velocity_rad_s: Vector3
    angular_acceleration_rad_s2: Vector3

    acceleration_frame: ClassVar[str] = "boot"
    acceleration_includes_gravity: ClassVar[bool] = False
    angular_velocity_frame: ClassVar[str] = "body"


@dataclass(frozen=True, slots=True)
class ImuHealth:
    """Last separate health update; its timestamp allows freshness checks."""

    timestamp_s: float
    timestamp_clock: Clock
    phase: ImuPhase
    sensors_online: int
    sensors_total: int
    sensors_calibrated: int
    calibration_percent: int
    calibration_remaining_ms: int
    output_valid: bool


class Imu(GenericSensor[ImuState]):
    """Single-consumer processed IMU reader, used on one event loop.

    Initialize once without recalibrating the module; repeatedly await read().
    Implementations decode state and cache sparse health updates. Estimation
    belongs in the producing device or simulator, outside the reader.
    """

    @property
    @abstractmethod
    def latest_health(self) -> ImuHealth | None:
        """Most recently consumed health update, or None before receipt."""
