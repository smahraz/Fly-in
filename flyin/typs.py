from enum import IntEnum, auto
import math


WHITE = (0xff, 0xff, 0xff, 0xff)


class Point:
    x: float
    y: float

    def __init__(self, x: float | int, y: float | int) -> None:
        self.x = float(x)
        self.y = float(y)

    def as_tuple(self) -> tuple[int, int]:
        return int(self.x), int(self.y)

    def __truediv__(self, other: int | float) -> "Point":
        self.x /= other
        self.y /= other
        return self

    def __add__(self, other: "Point") -> "Point":
        return Point(
            self.x + other.x,
            self.y + other.y
        )

    def __mul__(self, other: float) -> "Point":
        return Point(
            self.x * other,
            self.y * other
        )

    def __sub__(self, other: "Point") -> "Point":
        return Point(
            self.x - other.x,
            self.y - other.y
        )

    def distance(self, other: "Point") -> float:
        return math.sqrt(
            (self.x - other.x) ** 2 +
            (self.y - other.y) ** 2
        )

    def cp(self) -> "Point":
        return Point(
            self.x,
            self.y
        )


class Location:
    pos: Point
    drone_count: int
    max_drones: int

    def add_drone(self) -> None:
        assert self.drone_count <= self.max_drones
        self.drone_count += 1

    def sub_drone(self) -> None:
        assert self.drone_count > 0
        self.drone_count -= 1

    def is_full(self) -> bool:
        return self.max_drones - self.drone_count == 0


class Connection(Location):
    zones: tuple["Zone", "Zone"]
    pos: Point

    def __init__(
        self,
        z1: "Zone",
        z2: "Zone",
        max_link_capacity: int = 1
    ) -> None:
        self.zones = (z1, z2)
        self.pos = (z1.pos + z2.pos) / 2
        self.max_drones = max_link_capacity

        self.drone_count = 0

    def __repr__(self) -> str:
        return f"Connection('{', '.join(z.name for z in self.zones)}')"


class Zone(Location):

    class ZoneType(IntEnum):
        NORMAL = auto()
        BLOCKED = auto()
        RESTRICTED = auto()
        PRIORITY = auto()

    connections: set[Connection]

    ZONE_TYPES = {
        "normal": ZoneType.NORMAL,
        "blocked": ZoneType.BLOCKED,
        "restricted": ZoneType.RESTRICTED,
        "priority": ZoneType.PRIORITY
    }

    def __init__(
        self,
        name: str,
        pos: Point,
        zone: str = "normal",
        max_drones: int = 1,
        color: tuple[int, int, int, int] = WHITE
    ) -> None:
        self.name = name

        self.pos = pos
        self.connections = set()
        self.color = color

        self.drone_count = 0
        self.deadend = False

        assert zone in self.ZONE_TYPES
        assert max_drones > 0

        self.zone = self.ZONE_TYPES[zone]
        self.max_drones = max_drones

    def __str__(self) -> str:
        return f"Zone({self.name}: {self.pos.x},{self.pos.y})"

    def add_connection(self, connection: Connection) -> None:
        self.connections.add(connection)


class Drone:
    drone_id = 0
    current_location: Location
    prev_location: Location

    def __init__(self, start_hub: Location) -> None:
        self.__class__.drone_id += 1
        self.drone_id = self.drone_id

        self.current_location = start_hub
        self.prev_location = start_hub
        start_hub.add_drone()
        self.moving_to_restricted = False

    def move_to(self, new_location: Location) -> None:
        new_location.add_drone()
        self.current_location.sub_drone()

        self.prev_location = self.current_location
        self.current_location = new_location
