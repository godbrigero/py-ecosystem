# ecosystem

```python
from ecosystem.robot_process import RobotProcess, RobotMode


class MyRobot(RobotProcess):
    async def is_system_safe(self) -> bool:
        return True


MyRobot(poll_interval_s=0.02).run(RobotMode.TELEOP)
```

Define a process, say what "safe" means, and run it. From there you extend `SubsystemBase` and `GenericMotor` to build out the rest:

```python
from ecosystem.subsystem import SubsystemBase
from ecosystem.motor import GenericMotor


class Arm(SubsystemBase):
    async def poll(self):
        # read sensors, update state, every loop tick
        pass


class ArmMotor(GenericMotor):
    async def _run(self):
        # only called while the system is safe
        pass

    async def stop(self):
        pass
```

The loop, the polling, and the safety gating are handled for you.

## What this is

A drop-in core loop for robot-style Python processes, in the spirit of WPILib's subsystem model but without the rest of a framework attached. You copy it into your project, extend a few base classes, and you have a running process. There is no install step and no API to memorize.

The core idea: one long-running process owns your subsystems and motors. It polls every subsystem on a fixed interval, and only lets motors run while the system reports it is safe. Sensors can share a small typed base class without being tied to any specific sample shape.

## What you get

- One process that owns your subsystems and motors.
- A fixed-interval poll loop (and a warning when a cycle runs long).
- Motors that auto-register and stop the instant the system is unsafe.
- An abstract `GenericSensor[ReadT]` base with async `initialize()`,
  `read(timeout_s=1.0)`, and `close()`. Initialize once and read repeatedly;
  async context-manager cleanup is optional.
- Run modes like teleop and sim from the same process.

## Drop it in

```bash
make install-tools INSTALLATION_PATHS="/path/to/your/project"
```

Copies the `ecosystem/` folder into your project. Imports are relative, so it just works once it lands. Run it again later to update, or copy the folder by hand.

## Layout

- `ecosystem/subsystem.py` - base class for subsystems.
- `ecosystem/robot_process.py` - the central process and poll loop.
- `ecosystem/motor.py` - base motor that registers itself.
- `ecosystem/sensor.py` - typed base class for sensors.
- `ecosystem/imu.py` - processed IMU interface, state, and health.

Only the `ecosystem/` folder goes into your project. Everything else here is for developing ecosystem itself.

## Processed IMU modules

`ecosystem.imu.Imu` specializes `GenericSensor[ImuState]` for fused inertial
modules. Implement `initialize()`, `read(timeout_s=1.0)`, `close()`, and the
`latest_health` property. `ImuState` requires orientation, position, velocity,
linear acceleration, angular velocity, and angular acceleration. Its documented
frames and SI units are shared by hardware and simulation. `ImuHealth` is a
separate immutable cached update with its own source timestamp.

Keep USB, Autobahn, protobuf decoding, and estimators in downstream adapters.
The core has no transport dependencies and does no filtering or integration.
Use `GenericSensor[T]` for other sensors; add specialized contracts only when
their data or capabilities need a common semantic interface.

```python
from ecosystem.imu import Imu


async def consume(imu: Imu):
    await imu.initialize()
    try:
        while True:
            state = await imu.read()
            # Use state.orientation_wxyz, state.velocity_m_s, etc.
            # imu.latest_health is a separate cached update, possibly None.
    finally:
        await imu.close()
```

Pass a hardware or simulation implementation to the same loop.
