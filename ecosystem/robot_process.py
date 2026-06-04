import asyncio
from dataclasses import dataclass
from enum import Enum
import time
from typing import TYPE_CHECKING

from .subsystem import SubsystemBase

if TYPE_CHECKING:
    from .motor import GenericMotor


class RobotMode(Enum):
    TELEOP = "teleop"
    SIM = "sim"


@dataclass
class PollResult:
    poll_to_time: dict[SubsystemBase, float]
    total_time: float

    def __str__(self) -> str:
        result_lines = [
            f"Took {self.total_time} seconds to poll {len(self.poll_to_time)} subsystems"
        ]
        for subsystem, poll_time in self.poll_to_time.items():
            result_lines.append(f"{subsystem.name} took {poll_time} seconds")

        return "\n".join(result_lines)


class RobotProcess(SubsystemBase):
    MOTORS: set["GenericMotor"] = set()

    def __init__(self, poll_interval_s: float):
        super().__init__("robot_process")
        self.subsystems: set[SubsystemBase] = {self}

        self.poll_interval_s = poll_interval_s

        asyncio.run(self.on_init())

    async def is_system_safe(self) -> bool:
        raise NotImplementedError("Subclass must implement is_system_safe")

    async def on_init(self):
        pass

    async def on_teleop(self):
        pass

    async def on_sim(self):
        pass

    async def poll(self):
        pass

    def run(self, mode: RobotMode):
        asyncio.run(self._run(mode))

    async def _run(self, mode: RobotMode):
        mode_func = {
            RobotMode.TELEOP: self.on_teleop,
            RobotMode.SIM: self.on_sim,
        }[mode]
        await mode_func()
        await self.event_loop_poll()

    async def add_subsystem(self, subsystem: SubsystemBase):
        await subsystem.start()
        self.subsystems.add(subsystem)

    async def event_loop_poll(self):
        while True:
            poll_result = await self._poll_subsystems()
            if poll_result.total_time > self.poll_interval_s:
                print(poll_result)

            await self.poll_motors()

            await asyncio.sleep(self.poll_interval_s)

    async def _poll_subsystems(self) -> PollResult:
        poll_to_time: dict[SubsystemBase, float] = {}

        total_start_time = time.time()
        for subsystem in self.subsystems:
            start_time = time.time()
            await subsystem.poll()
            end_time = time.time()
            poll_to_time[subsystem] = end_time - start_time

        total_end_time = time.time()
        total_time = total_end_time - total_start_time
        return PollResult(poll_to_time, total_time)

    async def poll_motors(self):
        if len(RobotProcess.MOTORS) == 0:
            return

        is_system_safe = await self.is_system_safe()

        for motor in RobotProcess.MOTORS:
            if is_system_safe:
                await motor._run()
            else:
                await motor.stop()
