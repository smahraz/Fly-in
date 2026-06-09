from enum import IntEnum, auto


WHITE = (0xff, 0xff, 0xff, 0xff)


class Connection:
    zones: set[str]

    def __init__(self, z1: str, z2: str, max_link_capacity: int = 1) -> None:
        self.zones = {z1, z2}
        self.max_link_capacity = max_link_capacity
        self._drone_count = 0

    def __repr__(self) -> str:
        return f"Connection('{', '.join(self.zones)}')"

    def is_full(self) -> bool:
        return self.max_link_capacity - self._drone_count == 0

    def drone_passing_through(self) -> None:
        assert self._drone_count <= self.max_link_capacity
        self._drone_count += 1

    def drone_passed(self) -> None:
        assert self._drone_count > 0
        self._drone_count -= 1


class Zone:

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
        x: int,
        y: int,
        zone: str = "normal",
        max_drones: int = 1,
        color: tuple[int, int, int, int] = WHITE
    ) -> None:
        self.name = name

        self.x = x
        self.y = y
        self.connections = set()
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
        self.connections.add(connection)

    def drone_arrives(self) -> None:
        assert self._drone_count <= self.max_drones
        self._drone_count += 1

    def drone_leaves(self) -> None:
        assert self._drone_count > 0
        self._drone_count -= 1

    def is_full(self) -> bool:
        return self.max_drones - self._drone_count == 0


class Drone:
    drone_id = 0
    current_zone: Zone
    prev_zone: Zone | None
    prev_conn: Connection

    def __init__(self, start_hub: Zone) -> None:
        self.__class__.drone_id += 1
        self.drone_id = self.drone_id

        self.current_zone = start_hub
        start_hub.drone_arrives()
        self.prev_zone = None
        self.moving_to_restricted = False

    def move_to(self, new_zone: Zone, conn: Connection) -> None:
        assert new_zone.zone != Zone.ZoneType.BLOCKED
        self.prev_conn = conn

        if new_zone.zone == Zone.ZoneType.RESTRICTED:
            self.moving_to_restricted = True
        else:
            new_zone.drone_arrives()

        self.current_zone.drone_leaves()

        conn.drone_passing_through()
        self.prev_zone = self.current_zone
        self.current_zone = new_zone

    def clear_conn(self) -> None:
        if self.prev_zone is not None:
            if not self.moving_to_restricted:
                self.prev_conn.drone_passed()
