from typing import Iterable, Generator
from queue import Queue
from flyin import DataParser, Zone, Connection, Drone


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
                        conn1, conn2 = zone.connections
                        zn1 = self._get_other_zone(conn1, zone)
                        zn2 = self._get_other_zone(conn2, zone)
                        zone = zn1 if zn2 in visited else zn2
                    else:
                        zone = self._get_other_zone(list(zone.connections)[0], zone)

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

        path = self.find_all_paths()[0]
        drone_nb = self._parsing_data.number_of_drones
        drones = [Drone(self._parsing_data.start_hub) for _ in range(drone_nb)]

        paths = {
            d: path_to_queue(path)
            for d in drones
        }
        targets = {
            d: paths[d].get()
            for d in drones
        }

        moved: list[Drone]
        turn = 0
        while not self._parsing_data.end_hub.is_full():
            moved = []
            for d in drones:
                if d not in targets:
                    continue
                if not targets[d].is_full():
                    conn, *_ = targets[d].connections & d.current_zone.connections
                    if d.moving_to_restricted:
                        d.moving_to_restricted = False
                        d.current_zone.drone_arrives()
                        if targets[d] != self._parsing_data.end_hub:
                            targets[d] = paths[d].get()
                        else:
                            del targets[d]
                        moved.append(d)
                    elif not conn.is_full():
                        d.move_to(targets[d], conn)
                        if targets[d].zone != Zone.ZoneType.RESTRICTED:
                            if targets[d] != self._parsing_data.end_hub:
                                targets[d] = paths[d].get()
                            else:
                                del targets[d]
                        moved.append(d)

            turn += 1
            print(f"turn {turn}", "*"*7)
            for d in moved:
                print(d.drone_id, d.prev_zone, d.current_zone)
                d.clear_conn()
            yield drones

    def _find_all_paths(
        self,
        complete_paths: list[tuple[int, list[Zone]]],
        current_path: list[Zone],
        current_zone: Zone,
        visited: set[Zone],
    ) -> None:
        for conn in current_zone.connections:
            zone = self._get_other_zone(conn, current_zone)
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

    def _get_other_zone(self, conn: Connection, zone: Zone) -> Zone:
        z1, z2 = conn.zones
        return self._zones[z1 if z2 == zone.name else z2]

    @staticmethod
    def _path_cost(path: Iterable[Zone]) -> int:
        def cost(zone: Zone):
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

