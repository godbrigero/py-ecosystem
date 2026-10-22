"""Shared camera frame contract, independent of capture transports."""
from dataclasses import FrozenInstanceError

import pytest

from ecosystem.camera import Camera, CameraFrame, CameraInfo, PixelFormat, SensorColor


def frame(**overrides):
    fields = dict(
        timestamp_s=1.0, timestamp_clock="monotonic", sequence=0, frame_id="cam_optical",
        width_px=4, height_px=2, row_step_bytes=12, pixel_format=PixelFormat.RGB8,
        data=bytes(24),
    )
    fields.update(overrides)
    return CameraFrame(**fields)


def test_frame_accepts_padded_rows_and_zero_copy_buffers():
    padded = frame(row_step_bytes=16, data=memoryview(bytearray(32)))
    assert padded.row_step_bytes == 16
    with pytest.raises(FrozenInstanceError):
        padded.sequence = 1


@pytest.mark.parametrize("overrides, message", [
    ({"width_px": 0}, "positive"),
    ({"row_step_bytes": 11}, "smaller than one row"),
    ({"data": bytes(23)}, "smaller than row_step_bytes"),
    ({"timestamp_s": float("nan")}, "finite"),
])
def test_frame_rejects_inconsistent_geometry(overrides, message):
    with pytest.raises(ValueError, match=message):
        frame(**overrides)


def test_mono_rows_use_one_byte_per_pixel():
    assert frame(pixel_format=PixelFormat.MONO8, row_step_bytes=4, data=bytes(8))
    assert PixelFormat("bgr8").channels == 3


def test_camera_requires_info_and_lifecycle():
    class MissingInfo(Camera):
        async def initialize(self):
            pass

        async def read(self, timeout_s=1.0):
            return frame()

        async def close(self):
            pass

    with pytest.raises(TypeError):
        MissingInfo()

    class Complete(MissingInfo):
        @property
        def info(self):
            return CameraInfo("cam", "cam_optical", 4, 2, PixelFormat.RGB8, 30.0, SensorColor.COLOR)

    assert Complete().info.intrinsics is None


def test_monochrome_sensors_only_deliver_mono8():
    mono = CameraInfo("bw", "bw_optical", 4, 2, PixelFormat.MONO8, 60.0, SensorColor.MONO)
    assert mono.sensor_color is SensorColor.MONO
    with pytest.raises(ValueError, match="must deliver mono8"):
        CameraInfo("bw", "bw_optical", 4, 2, PixelFormat.RGB8, 60.0, SensorColor.MONO)
    assert CameraInfo("c", "c_optical", 4, 2, PixelFormat.MONO8, 30.0, SensorColor.COLOR)
