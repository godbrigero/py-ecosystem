from typing import Generic, TypeVar


ReadT = TypeVar("ReadT")


class GenericSensor(Generic[ReadT]):
    def initialize(self) -> None:
        raise NotImplementedError("Subclass must implement initialize")

    def read(self) -> ReadT:
        raise NotImplementedError("Subclass must implement read")

    def close(self) -> None:
        pass
