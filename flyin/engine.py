from typing import Iterable, Generator
from queue import Queue
from flyin import DataParser, Zone, Drone
from flyin.typs import Connection


class Engine:
    def __init__(self, parsing_data: DataParser) -> None:
        self._parsing_data = parsing_data
        self._zones = parsing_data.zones
        self.mark_deadends()

    def mark_deadends(self) -> None:
        visited: set[Zone] = set()
        for zone in self._zones.values():
            if (
                len(zone.connections) == 1
                and zone is not self._parsing_data.end_hub
                and zone is not self._parsing_data.start_hub
                and zone not in visited
            ):
                while len(zone.connections) <= 2:
                    visited.add(zone)
                    zone.deadend = True
                    if len(zone.connections) == 2:
                        zones2, zones1 = (
                            set(con.zones) for con in zone.connections
                        )
                        zone, *_ = (zones1 ^ zones2) - visited
                    else:
                        conn, *_ = zone.connections
                        zone, *_ = set(conn.zones) - visited

    def find_all_paths(self) -> list[tuple[int, list[Zone]]]:
        paths: list[tuple[int, list[Zone]]] = []
        self._find_all_paths(
            paths,
            [
                self._parsing_data.start_hub,
            ],
            self._parsing_data.start_hub,
            {self._parsing_data.start_hub},
        )
        return sorted(
            paths,
            key=lambda tpl: tpl[0]
        )

    def simulation(self) -> Generator[list[Drone], None, None]:
        def path_to_queue(path: tuple[int, list[Zone]]) -> Queue[Zone]:
            q: Queue[Zone] = Queue()
            for zone in path[1][1:]:
                q.put(zone)
            return q

        def get_from_queue(drone: Drone) -> None:
            if targets[drone] != self._parsing_data.end_hub:
                targets[drone] = paths[drone].get()

        path = self.find_all_paths()[0]
        drone_nb = self._parsing_data.number_of_drones
        drones = [Drone(self._parsing_data.start_hub) for _ in range(drone_nb)]

        yield drones

        paths = {
            d: path_to_queue(path)
            for d in drones
        }
        targets = {
            d: paths[d].get()
            for d in drones
        }

        turn = 0
        while not self._parsing_data.end_hub.is_full():
            for d in drones:
                if targets[d].zone is Zone.ZoneType.RESTRICTED:
                    if isinstance(d.current_location, Connection):
                        if not targets[d].is_full():
                            d.move_to(targets[d])
                            get_from_queue(d)
                    elif isinstance(d.current_location, Zone):
                        conn, *_ = targets[d].connections & d.current_location.connections
                        if not conn.is_full():
                            d.move_to(conn)
                else:
                    if not targets[d].is_full():
                        d.move_to(targets[d])
                        get_from_queue(d)
            turn += 1
            yield []

    def _find_all_paths(
        self,
        complete_paths: list[tuple[int, list[Zone]]],
        current_path: list[Zone],
        current_zone: Zone,
        visited: set[Zone],
    ) -> None:
        for conn in current_zone.connections:
            zone = conn.zones[0] \
                if conn.zones[1] == current_zone else conn.zones[1]
            if (
                zone in visited
                or zone.deadend
                or zone.zone is Zone.ZoneType.BLOCKED
            ):
                continue
            if zone == self._parsing_data.end_hub:
                current_path_new = current_path.copy()
                current_path_new.append(zone)
                complete_paths.append((
                    self._path_cost(current_path_new),
                    current_path_new
                ))
            else:
                visited_new = visited.copy()
                visited_new.add(zone)
                current_path_new = current_path.copy()
                current_path_new.append(zone)
                self._find_all_paths(
                    complete_paths, current_path_new, zone, visited_new
                )

    @staticmethod
    def _path_cost(path: Iterable[Zone]) -> int:
        def cost(zone: Zone) -> int:
            if zone.zone == Zone.ZoneType.RESTRICTED:
                return 2
            return 1
        return sum(cost(z) for z in path)


if __name__ == "__main__":
    with open("maps/challenger/01_the_impossible_dream.txt", "r") as f:
        d = DataParser(f.read())
        e = Engine(d)
        for i in e.simulation():
            pass
