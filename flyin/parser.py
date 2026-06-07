import re
from typing import Any
from flyin import Zone, Connection


class ParseError(Exception):
    def __init__(self, line_number: int, msg: str) -> None:
        self.line_number = line_number
        self.msg = msg
        super().__init__(f"{line_number}: {msg}")


class DataParser:

    class ZoneParser:
        _coordinate: set[tuple[int, int]]
        _created_zones: set[str]

        start_hub: Zone | None
        end_hub: Zone | None

        ALLOWED_METADATA_KEYS = {"zone", "color", "max_drones"}
        ZONE_TYPE = {"normal", "blocked", "restricted", "priority"}

        def __init__(self) -> None:
            self._coordinate = set()
            self._created_zones = set()
            self.start_hub = None
            self.end_hub = None

        def extract(
            self,
            line_num: int,
            line: str
        ) -> Zone:
            zone_str, *metadata = line.split("[")
            params = [ln for ln in zone_str.split() if ln]

            hub_type = self._check_hub_type(params[0], line_num)

            # remove leading part 'exmple: xx xx xx' -> 'xx xx xx'.
            try:
                params = params[params.index(":") + 1:]
            except Exception:
                params = params[1:]

            z_name, x, y = self._check_params(params, line_num)
            if z_name in self._created_zones:
                raise ParseError(line_num, f"'{z_name}' is already defined")
            if (x, y) in self._coordinate:
                raise ParseError(line_num, "two zones overlap")

            extracted_metadata = self._metadata(
                "[".join(["",] + metadata), line_num
            ) if metadata else {}

            self._created_zones.add(z_name)
            self._coordinate.add((x, y))

            zone = Zone(
                z_name,
                x,
                y,
                **extracted_metadata
            )
            match hub_type:
                case "start_hub":
                    self.start_hub = zone
                case "end_hub":
                    self.end_hub = zone
            return zone

        @staticmethod
        def _metadata(metadata: str, ln: int) -> dict[str, Any]:
            metadata = DataParser._prepare_metadata(metadata, ln)
            data: dict[str, Any] = {}

            for entry in metadata.split():
                DataParser._check_metadata_entry(entry, ln)
                value: Any
                key, value = entry.split("=")

                if key in data:
                    raise ParseError(ln, f"(metadata) re-assign '{key}'")

                if key not in DataParser.ZoneParser.ALLOWED_METADATA_KEYS:
                    raise ParseError(ln, f"(metadata) unknown key `{key}`")

                match key:
                    case "zone":
                        if value not in DataParser.ZoneParser.ZONE_TYPE:
                            raise ParseError(
                                ln, "(metadata) unknown zone type"
                            )
                    case "max_drones":
                        try:
                            value = int(value)
                            if value < 1:
                                raise ParseError(
                                    ln, "(metadata) max_drones is less than 1"
                                )
                        except ValueError:
                            raise ParseError(
                                ln,
                                "(metadata) max_drones value isn't a number"
                            )
                    case "color":
                        pass
                data[key] = value
            return data

        def _check_hub_type(self, zone_type: str, line_num: int) -> str:
            if zone_type.startswith("start_hub"):
                if self.start_hub is not None:
                    raise ParseError(line_num, "`start_hub` already exists")
                return "start_hub"
            if zone_type.startswith("end_hub"):
                if self.end_hub is not None:
                    raise ParseError(line_num, "`end_hub` already exists")
                return "end_hub"
            return "hub"

        @staticmethod
        def _check_params(
            params: list[str],
            line_num: int
        ) -> tuple[str, int, int]:
            if len(params) != 3:
                raise ParseError(line_num, "`hub` takes 3 parameter")
            if not re.fullmatch(r'\w+', params[0]):
                raise ParseError(
                    line_num,
                    "Hub name may contain only letters, numbers, & underscores"
                )
            if not all(re.fullmatch(r"[+-]?\d+", pr) for pr in params[1:3]):
                raise ParseError(line_num, "x and y should be numbers")
            return params[0], int(params[1]), int(params[2])

    class ConnectionParser:

        _established_connections: set[str]

        def __init__(self, zones: dict[str, Zone]) -> None:
            self._zones = zones
            self._established_connections = set()

        def extract(self, line_num: int, line: str) -> None:
            conn_str, *metadata = line.split("[")
            conn_str = re.sub(r'connection\s+:', 'connection:', conn_str)
            conn_str = re.sub(r'\s{2,}:', ' ', conn_str)
            params = conn_str.split()[1:]

            zones2connect = self._check_params(params, line_num)
            if "-".join(zones2connect) in self._established_connections:
                raise ParseError(line_num, "connection is already established")
            self._cache_connection(*zones2connect)

            max_link_capacity = self._metadata(
                "[".join(["",] + metadata), line_num
            ) if metadata else 1

            _ = tuple(zones2connect)

            cn = Connection(_[0], _[1], max_link_capacity)
            for zone in zones2connect:
                self._zones[zone].add_connection(cn)

        @staticmethod
        def _metadata(metadata: str, ln: int) -> int:
            metadata = DataParser._prepare_metadata(metadata, ln)
            max_link_capacity: int | None = None

            for entry in metadata.split():
                DataParser._check_metadata_entry(entry, ln)

                key, value = entry.split('=')

                if key != "max_link_capacity":
                    raise ParseError(ln, f"(metadata) unknown key '{key}'")
                else:
                    if max_link_capacity is not None:
                        raise ParseError(
                            ln,
                            "(metadata) `max_link_capacity` is already defined"
                        )
                    else:
                        try:
                            max_link_capacity = int(value)
                            if max_link_capacity < 1:
                                raise ParseError(
                                    ln,
                                    "(metadata) max_link_capacity less than 1"
                                )
                        except ValueError:
                            raise ParseError(
                                ln, "(metadata) value is not a number"
                            )
            if max_link_capacity is None:
                return 1
            return max_link_capacity

        def _check_params(self, params: list[str], ln: int) -> set[str]:
            if len(params) != 1:
                raise ParseError(ln, "connection needs only one argument")
            conn = params[0]
            match_ = re.fullmatch(r"(\w+)-(\w+)", conn)
            if match_ is None:
                raise ParseError(
                    ln, "connection should formated like zone1-zone2"
                )

            zones2connect = {match_.group(1), match_.group(2)}
            for z_name in zones2connect:
                if z_name not in self._zones:
                    raise ParseError(ln, f"'{z_name}', zone is not defined")
            return zones2connect

        def _cache_connection(self, zone1: str, zone2: str) -> None:
            self._established_connections.add(f"{zone1}-{zone2}")
            self._established_connections.add(f"{zone2}-{zone1}")

    lines: list[tuple[int, str]]
    number_of_drones: int
    zones: dict[str, Zone]
    start_hub: Zone
    end_hub: Zone

    def __init__(self, metadata: str) -> None:
        self.zones = {}

        self._sanitize_lines(metadata.split("\n"))
        if self.lines == []:
            raise ParseError(0, "noting to extract, file empty")
        self.number_of_drones = self._nb_drones(self.lines[0])
        self.lines = self.lines[1:]
        self._extract_zones_and_conections()

    def _extract_zones_and_conections(self) -> None:
        # these two `sets` below, is only for caching
        zp = self.ZoneParser()
        cp = self.ConnectionParser(self.zones)

        for line_num, line in self.lines:
            if re.match(r"^(start_|end_)?hub\s*:", line):
                zone = zp.extract(line_num, line)
                self.zones[zone.name] = zone
            elif re.fullmatch(r"^connection\s*:.+", line):
                cp.extract(line_num, line)
            elif re.fullmatch(r"^nb_drones\s*:.+", line):
                raise ParseError(line_num, "re-assign `nb_drones`")
            elif re.match(r"^[\w\s]+\s*:.+", line):
                raise ParseError(
                    line_num, f"Unknown keyword `{line.split(':')[0].strip()}`"
                )
            else:
                raise ParseError(line_num, "broken line")
        if zp.start_hub is None:
            raise ParseError(0, "missing start_hub")
        if zp.end_hub is None:
            raise ParseError(0, "missing end_hub")
        self.start_hub = zp.start_hub
        self.end_hub = zp.end_hub

    def _nb_drones(self, line: tuple[int, str]) -> int:
        if not re.match(r"^nb_drones\s*:", line[1]):
            raise ParseError(0, "missing `nb_drones` as the first key")
        match_ = re.fullmatch(r"nb_drones\s*:\s*([+-]?\d+)", line[1])
        if match_ is None:
            raise ParseError(
                line[0], "Value of `nb_drones` should be a positive number"
            )
        number = int(match_.group(1))
        if number <= 0:
            raise ParseError(line[0], "Assert that `nb_drones` > 0")
        return number

    def _sanitize_lines(self, lines: list[str]) -> None:
        self.lines: list[tuple[int, str]] = []
        for line_num, line in enumerate(lines, start=1):
            line = line.split("#")[0].strip()
            if line:
                self.lines.append((line_num, line))

    @staticmethod
    def _prepare_metadata(metadata: str, ln: int) -> str:
        if not metadata.endswith("]"):
            raise ParseError(
                ln,
                "(metadata) missing square bracket near the end"
            )
        metadata = metadata[1:-1]
        if metadata.count("[") or metadata.count("]"):
            raise ParseError(
                ln,
                "(metadata) no square brackets should be inside metadata"
            )
        metadata = metadata.strip()
        # remove spaces around equal sign.
        metadata = re.sub(r"([^\s])\s*=\s*([^\s])", r"\1=\2", metadata)
        # replace consecutive spaces with a single space.
        return re.sub(r"\s{2,}", " ", metadata)

    @staticmethod
    def _check_metadata_entry(entry: str, line_num: int) -> None:
        equal_sign = entry.count("=")
        if equal_sign == 1 and entry.startswith("="):
            raise ParseError(
                line_num,
                "(metadata) assignment without key name"
            )
        if equal_sign == 0 or (equal_sign == 1 and entry.endswith("=")):
            raise ParseError(
                line_num,
                f"(metadata) forgot to assign a val to '{entry.split('=')[0]}'"
            )
        if equal_sign > 1:
            raise ParseError(line_num, "(metadata) too many equal signs '='")


if __name__ == "__main__":
    PATH = "maps/easy/01_linear_path.txt"
    with open(PATH, "r") as file:
        metadata = file.read()

    try:

        d = DataParser(metadata)
    except ParseError as e:
        print(e)
        exit()
    for z in d.zones.values():
        print(z)
        print(z.connections)
