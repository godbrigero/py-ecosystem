class SubsystemBase:
    def __init__(self, name: str):
        self.name = name

    def __eq__(self, other):
        return self is other

    def __hash__(self):
        return id(self)

    async def poll(self):
        pass

    async def start(self):
        pass
