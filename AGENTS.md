# Agent Guide

This repository contains `ecosystem`, a tiny vendored Python core for
robot-style long-running processes. It is meant to be copied into another
project, not installed as a package.

Use this file as the agent-facing source of truth. `README.md` is the concise
human-facing overview.

## What This Is

`ecosystem` provides a small async process loop with subsystem polling and motor
safety gating:

- `RobotProcess` owns one long-running async process.
- `SubsystemBase` is the base class for objects that need periodic `poll()`
  calls.
- `GenericMotor` is the base class for safety-gated actuator behavior.
- `GenericSensor[ReadT]` is the base class for synchronous sensors with a
  caller-specified read result type.
- `RobotMode` selects startup hooks such as `on_teleop()` and `on_sim()`.

The intended downstream shape is:

```text
your-project/
  ecosystem/
    robot_process.py
    subsystem.py
    motor.py
    sensor.py
  your_robot_code.py
```

Only the `ecosystem/` directory is meant to be copied into another project.
Files such as `Makefile`, `pyproject.toml`, and `import_linter_contracts/` are
for developing this repository itself.

## How To Install Into A Project

From this repository, run:

```bash
make install-tools INSTALLATION_PATHS="/path/to/your/project"
```

This copies this repo's `ecosystem/` directory to
`/path/to/your/project/ecosystem/` using `rsync --delete`, so removed files in
this source repo are also removed from the target copy.

You can install into multiple projects by separating paths with spaces:

```bash
make install-tools INSTALLATION_PATHS="/path/to/project-a /path/to/project-b"
```

Manual installation is also valid: copy the `ecosystem/` directory into the root
of the downstream project.

## How To Use It

Create a process by subclassing `RobotProcess`, defining what "safe" means, and
running a mode:

```python
from ecosystem.robot_process import RobotMode, RobotProcess


class MyRobot(RobotProcess):
    async def is_system_safe(self) -> bool:
        return True


MyRobot(poll_interval_s=0.02).run(RobotMode.TELEOP)
```

Add subsystems by subclassing `SubsystemBase` and registering instances from a
process hook such as `on_init()`:

```python
from ecosystem.robot_process import RobotProcess
from ecosystem.subsystem import SubsystemBase


class Arm(SubsystemBase):
    async def poll(self):
        pass


class MyRobot(RobotProcess):
    async def on_init(self):
        await self.add_subsystem(Arm("arm"))

    async def is_system_safe(self) -> bool:
        return True
```

Add motors by subclassing `GenericMotor`. A motor auto-registers when it is
constructed. `_run()` is called only while the system is safe; `stop()` is called
when the system is unsafe.

```python
from ecosystem.motor import GenericMotor


class ArmMotor(GenericMotor):
    async def _run(self):
        pass

    async def stop(self):
        pass
```

Add sensors by subclassing `GenericSensor` with the concrete read type returned
by `read()`:

```python
from dataclasses import dataclass

from ecosystem.sensor import GenericSensor


@dataclass
class ImuSample:
    temperature_c: float


class Imu(GenericSensor[ImuSample]):
    def initialize(self) -> None:
        pass

    def read(self) -> ImuSample:
        return ImuSample(temperature_c=20.0)
```

## Runtime Semantics

`RobotProcess.run(mode)` starts the selected mode hook, then enters the shared
poll loop. Each loop cycle:

1. Calls `poll()` on each registered subsystem.
2. Prints timing information if subsystem polling exceeds `poll_interval_s`.
3. Calls `is_system_safe()`.
4. Calls each motor's `_run()` when safe, or `stop()` when unsafe.
5. Sleeps for `poll_interval_s`.

## Repository Layout

- `ecosystem/robot_process.py` contains `RobotProcess`, `RobotMode`, and poll
  timing.
- `ecosystem/subsystem.py` contains `SubsystemBase`.
- `ecosystem/motor.py` contains `GenericMotor`.
- `ecosystem/sensor.py` contains `GenericSensor`.
- `import_linter_contracts/relative_only.py` enforces relative imports inside
  `ecosystem/`.
- `Makefile` provides `install-tools` and `lint-imports`.
- `requirements.dev.txt` lists development tooling.
- `requirements.txt` is intentionally empty because the vendored runtime has no
  external dependency.

## Rules For Agents Editing This Repo

- Keep `ecosystem/` copy-friendly. Do not require packaging, installation, or
  files outside `ecosystem/` at runtime.
- Keep imports inside `ecosystem/` relative, for example
  `from .subsystem import SubsystemBase`. Absolute imports like
  `from ecosystem.subsystem import ...` break the vendored-copy workflow.
- Do not put downstream robot-specific hardware logic into this core unless the
  user explicitly asks for an example.
- If adding a runtime file that downstream projects need, place it under
  `ecosystem/` so `make install-tools` copies it naturally.
- Treat `import_linter_contracts/` as development tooling only.
- Prefer small explicit async base-class behavior over broad framework
  abstractions.

## Validation

After touching imports or adding Python files under `ecosystem/`, run:

```bash
make lint-imports
```

After changing install behavior, run a smoke copy:

```bash
make install-tools INSTALLATION_PATHS="/tmp/ecosystem-smoke"
```

Then inspect `/tmp/ecosystem-smoke/ecosystem/` to confirm the copied shape is
what downstream projects should receive.
