from enum import IntEnum, auto


WHITE = (0xff, 0xff, 0xff, 0xff)


class Connection:
    zones: set[str]
    metadata: dict[str, str]

    def __init__(self, z1: str, z2: str, max_link_capacity: int = 1) -> None:
        self.zones = {z1, z2}
        self.max_link_capacity = max_link_capacity

    def __repr__(self) -> str:
        return f"Connection('{', '.join(self.zones)}')"


class Zone:

    class ZoneType(IntEnum):
        NORMAL = auto()
        BLOCKED = auto()
        RESTRICTED = auto()
        PRIORITY = auto()

    connections: list[Connection]

    ZONE_TYPES = {
        "normal": ZoneType.NORMAL,
        "blocked": ZoneType.BLOCKED,
        "restricted": ZoneType.RESTRICTED,
        "priority": ZoneType.PRIORITY
    }

    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        zone: str = "normal",
        max_drones: int = 1,
        color: tuple[int, int, int, int] = WHITE
    ) -> None:
        self.name = name

        self.x = x
        self.y = y
        self.connections = []
        self.color = color

        self._drone_count = 0
        self.deadend = False

        assert zone in self.ZONE_TYPES
        assert max_drones > 0

        self.zone = self.ZONE_TYPES[zone]
        self.max_drones = max_drones

    def __str__(self) -> str:
        return f"Zone({self.name}: {self.x},{self.y})"

    def add_connection(self, connection: Connection) -> None:
        self.connections.append(connection)
