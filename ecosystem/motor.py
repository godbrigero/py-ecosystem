from .robot_process import RobotProcess


class GenericMotor:
    def __init__(self):
        RobotProcess.MOTORS.add(self)

    async def _run(self):
        raise NotImplementedError("Subclass must implement run")

    async def stop(self):
        raise NotImplementedError("Subclass must implement stop")
