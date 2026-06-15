from typing import Iterable, Generator
from functools import cmp_to_key
from flyin import DataParser, Zone, Drone, Connection
from .exceptions import MapError


class Graph:
    graph: dict[
        Zone,
        dict[Zone, int]
    ]

    def __init__(self) -> None:
        self.graph = {}

    def add_zone(self, zone: Zone, next_zone: Zone, cost: int) -> None:
        if zone not in self.graph:
            self.graph[zone] = {next_zone: cost}
            return
        old_cost = self.graph[zone].get(next_zone, float("inf"))
        if cost < old_cost:
            self.graph[zone][next_zone] = cost

    def get_next_target(self, current_zone: Zone) -> tuple[
        int,
        dict[Zone, int]
    ]:
        next_zones = self.graph[current_zone]
        return min(next_zones.values()), next_zones

    @staticmethod
    def from_path(paths: list[tuple[int, list[Zone]]]) -> "Graph":
        graph = Graph()

        for cost, p in paths[:50]:
            prev_zone = p[0]
            for z in p[1:]:
                cost -= prev_zone.cost()
                graph.add_zone(prev_zone, z, cost)
                prev_zone = z

        return graph


class Engine:
    def __init__(self, parsing_data: DataParser) -> None:
        self._parsing_data = parsing_data
        self._zones = parsing_data.zones

    @staticmethod
    def cmp_paths(
        path_a: tuple[int, list[Zone]],
        path_b: tuple[int, list[Zone]],
    ) -> int:
        T = Zone.ZoneType.PRIORITY
        if path_a[0] != path_b[0]:
            return path_a[0] - path_b[0]
        for i in range(min(len(path_a[1]), len(path_b[1]))):
            z1, z2 = path_a[1][i], path_b[1][i]
            if (
                (z1.zone is T and z2.zone is not T)
                or (z1.zone is not T and z2.zone is T)
            ):
                if z1.zone is T:
                    return -1
                return 1
        return 0

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
        if not paths:
            raise MapError(
                "there is no path between end_hub and start_hub"
            )
        return sorted(
            paths,
            key=cmp_to_key(self.cmp_paths)
        )

    def simulation(self) -> Generator[list[Drone], None, None]:
        drone_nb = self._parsing_data.number_of_drones
        drones = [Drone(self._parsing_data.start_hub) for _ in range(drone_nb)]

        yield drones

        graph = Graph.from_path(self.find_all_paths())

        cur_zone: dict[Drone, Zone] = {
            d: self._parsing_data.start_hub
            for d in drones
        }

        turn = 0
        end_hub = self._parsing_data.end_hub
        while not end_hub.drone_count == self._parsing_data.number_of_drones:
            moved: list[Drone] = []
            for d in drones:

                if d.current_location is self._parsing_data.end_hub:
                    continue

                if isinstance(d.current_location, Connection):
                    if not cur_zone[d].is_full():
                        d.move_to(cur_zone[d])
                        moved.append(d)
                    continue

                min_cost, next_zones = graph.get_next_target(cur_zone[d])
                for nxt_zone, cost in next_zones.items():
                    if nxt_zone.zone is Zone.ZoneType.RESTRICTED:
                        cn, *_ = cur_zone[d].connections & nxt_zone.connections
                        if not cn.is_full() and cost <= min_cost + 1:
                            cur_zone[d] = nxt_zone
                            d.move_to(cn)
                            moved.append(d)
                            break
                    else:
                        if not nxt_zone.is_full() and cost <= min_cost + 1:
                            cur_zone[d] = nxt_zone
                            d.move_to(nxt_zone)
                            moved.append(d)
                            break

            turn += 1
            for d in drones:
                d.clear_restricted_connection()
            yield moved

    def _find_all_paths(
        self,
        complete_paths: list[tuple[int, list[Zone]]],
        current_path: list[Zone],
        current_zone: Zone,
        visited: set[Zone],
    ) -> None:
        for conn in current_zone.connections:
            zone, *_ = (z for z in conn.zones if z != current_zone)
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
        return sum(z.cost() for z in path)


if __name__ == "__main__":
    with open("maps/hard/02_capacity_hell.txt", "r") as f:
        d = DataParser(f.read())
        e = Engine(d)
        x = 0
        for i in e.simulation():
            x += 1
        g = Graph.from_path(e.find_all_paths())
        from rich import print
        print(g.graph)
