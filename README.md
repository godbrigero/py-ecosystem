# Ecosystem

A small, drop-in core for building robot-style processes in Python. It is meant
to be copied directly into your own project, much like the core scheduling and
subsystem ideas behind WPILib, but without the rest of a framework attached to
it.

The idea is simple: you have a long-running process that owns a set of
subsystems and motors. The process repeatedly polls those subsystems on a fixed
interval, and only lets motors run while the system reports that it is safe to
do so. `ecosystem` gives you that loop and the base classes to hang your own
logic on, and stays out of the way of everything else.

## What this is meant to do

- Give you a single process that drives your whole robot or device.
- Poll every registered subsystem on a fixed interval and warn you when a poll
  cycle runs longer than that interval.
- Register motors automatically and gate them behind a safety check, so they
  stop the moment the system is no longer safe.
- Support different run modes (for example, teleop and sim) from the same
  process.

## What this is not

- It is not a package you install from a registry. There is no public API
  reference to learn here. It is a handful of small files you read, copy, and
  extend.
- It is not a full robotics framework. It is the minimal core loop and the base
  classes, nothing more.

## How it is laid out

Everything you drop into your project lives in the `ecosystem/` folder:

- `subsystem.py` defines the base class every subsystem extends.
- `robot_process.py` defines the central process and its polling loop.
- `motor.py` defines the base motor that registers itself with the process.

The rest of this repository (the Makefile, the import linter contract, the dev
requirements) exists to develop and ship `ecosystem` itself. You do not need to
copy those into your project.

## Adding it to your own project

Because `ecosystem` is meant to be vendored rather than installed, all of its
internal imports are relative. That means you can copy the `ecosystem/` folder
anywhere inside your project and it will keep working without being installed as
a top-level package.

The repository includes a Makefile target that copies the folder into one or
more projects for you:

```bash
make install-tools INSTALLATION_PATHS="/path/to/your/project /path/to/another"
```

This syncs the `ecosystem/` folder into an `ecosystem/` directory inside each
path you list. To pull in a newer version later, run the same command again; it
keeps the destination in sync with this source.

If you prefer, you can also just copy the `ecosystem/` folder by hand. There is
nothing special about how it gets there.

## A quick taste

You define a process, describe what "safe" means for your system, register your
subsystems, and run it. A minimal version looks like this:

```python
import asyncio

from ecosystem.robot_process import RobotProcess, RobotMode


class MyRobot(RobotProcess):
    async def is_system_safe(self) -> bool:
        return True

    async def on_teleop(self):
        # set up anything your robot needs before the loop starts
        pass


robot = MyRobot(poll_interval_s=0.02)
robot.run(RobotMode.TELEOP)
```

From there you create your own subsystems and motors by extending the base
classes, register subsystems with the process, and put your logic in their poll
methods. The loop and the safety gating are handled for you.

## Developing ecosystem itself

If you are changing `ecosystem` rather than just using it, install the dev
tooling and keep the internal imports relative:

```bash
pip install -r requirements.dev.txt
make lint-imports
```

The import check exists to protect the drop-in promise: absolute internal
imports would break the moment the folder is copied into a project that does not
install `ecosystem` as a top-level package.
