"""Portable contract for a camera that produces uncompressed image frames."""
from __future__ import annotations

import math
from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Literal, Union

from .sensor import GenericSensor

# monotonic: the host's CLOCK_MONOTONIC (time.monotonic() on Linux), which
# libcamera and V4L2 use for buffer timestamps. simulation: simulator time.
Clock = Literal["monotonic", "simulation"]
# Any contiguous byte buffer; a memoryview over a NumPy array avoids a copy.
PixelBuffer = Union[bytes, bytearray, memoryview]


class PixelFormat(str, Enum):
    """Packed 8-bit layouts. Channel order is the order of bytes in memory."""

    MONO8 = "mono8"
    RGB8 = "rgb8"
    BGR8 = "bgr8"

    @property
    def channels(self) -> int:
        return 1 if self is PixelFormat.MONO8 else 3


class SensorColor(str, Enum):
    """What the image sensor can see: monochrome sensors have no color filter."""

    MONO = "mono"
    COLOR = "color"


@dataclass(frozen=True, slots=True)
class CameraIntrinsics:
    """Pinhole intrinsics in pixels for the delivered image size."""

    fx_px: float
    fy_px: float
    cx_px: float
    cy_px: float


@dataclass(frozen=True, slots=True)
class CameraInfo:
    """What the camera actually delivers once initialized.

    frame_id names the optical frame (x right, y down, z forward through the
    lens). Monochrome sensors only deliver mono8. Intrinsics are None when
    unknown; nominal values are not a calibration.
    """

    name: str
    frame_id: str
    width_px: int
    height_px: int
    pixel_format: PixelFormat
    frame_rate_hz: float
    sensor_color: SensorColor
    intrinsics: CameraIntrinsics | None = None

    def __post_init__(self) -> None:
        if self.sensor_color is SensorColor.MONO and self.pixel_format is not PixelFormat.MONO8:
            raise ValueError(f"Monochrome camera {self.name!r} must deliver mono8")


@dataclass(frozen=True, slots=True)
class CameraFrame:
    """One uncompressed image. Rows may be padded: row i starts at
    i * row_step_bytes. The buffer must not be mutated after construction.
    """

    timestamp_s: float
    timestamp_clock: Clock
    sequence: int
    frame_id: str
    width_px: int
    height_px: int
    row_step_bytes: int
    pixel_format: PixelFormat
    data: PixelBuffer

    def __post_init__(self) -> None:
        if not math.isfinite(self.timestamp_s):
            raise ValueError("timestamp_s must be finite")
        if self.width_px <= 0 or self.height_px <= 0:
            raise ValueError("Frame dimensions must be positive")
        if self.row_step_bytes < self.width_px * self.pixel_format.channels:
            raise ValueError("row_step_bytes is smaller than one row of pixels")
        if memoryview(self.data).nbytes < self.row_step_bytes * self.height_px:
            raise ValueError("Frame data is smaller than row_step_bytes * height_px")


class Camera(GenericSensor[CameraFrame]):
    """Single-consumer frame reader, used on one event loop.

    read() returns the newest frame not yet returned, dropping older ones, so
    slow consumers process fresh images instead of building a backlog. It
    raises TimeoutError if no new frame arrives in time; it never repeats a
    frame. Implementations own capture, decoding, and pixel conversion.
    """

    @property
    @abstractmethod
    def info(self) -> CameraInfo:
        """Delivered stream description; valid after initialize()."""
