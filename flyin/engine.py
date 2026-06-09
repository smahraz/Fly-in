from flyin import DataParser, Zone, Connection


class Engine:
    def __init__(self, parsing_data: DataParser) -> None:
        self._parsing_data = parsing_data
        self._zones = parsing_data.zones

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
                        zone = self._get_other_zone(zone.connections[0], zone)

    def find_all_paths(self) -> None:
        paths: list[list[Zone]] = []
        self._find_all_paths(
            paths,
            [
                self._parsing_data.start_hub,
            ],
            self._parsing_data.start_hub,
            {self._parsing_data.start_hub},
        )
        print(len(paths))

    def _find_all_paths(
        self,
        complete_paths: list[list[Zone]],
        current_path: list[Zone],
        current_zone: Zone,
        visited: set[Zone],
    ) -> None:
        for conn in current_zone.connections:
            zone = self._get_other_zone(conn, current_zone)
            if zone in visited or zone.deadend:
                continue
            if zone == self._parsing_data.end_hub:
                complete_paths.append(current_path)
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


if __name__ == "__main__":
    with open("maps/challenger/01_the_impossible_dream.txt", "r") as f:
        d = DataParser(f.read())
        e = Engine(d)
        e.mark_deadends()
        e.find_all_paths()
