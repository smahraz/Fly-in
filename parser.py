import re
from typing import Any, Callable


class ParseError(Exception):
    def __init__(self, line_number: int, msg: str) -> None:
        self.line_number = line_number
        self.msg = msg
        super().__init__(f"{line_number}: {msg}")


def extract_inline_metadata(
    inline_metadata: str, raise_error: Callable[[str], ParseError]
) -> dict[str, str]:
    if not re.fullmatch(
        r"\[(\s*\w+\s*=\s*\w+)(\s+\w+\s*=\s*\w+)*\s*\]", inline_metadata
    ):
        if re.fullmatch(r"\[\s*\]", inline_metadata):
            raise raise_error("empty brackets []")
        else:
            raise raise_error("broken metadata format key=value")
    metadata = {}
    for m in re.finditer(r"(\w+)\s*=\s*(\w+)", inline_metadata):
        key, value = m.groups()
        if key in metadata:
            raise raise_error(f"duplicate key '{key}' in metadata")
        else:
            metadata[key] = value
    return metadata


class Connection:
    zones: set[str]
    metadata: dict[str, str]

    def __init__(self, zones: tuple[str, str], **metadata: str) -> None:
        self.zones = set(zones)
        # convert to parse error or something
        assert len(self.zones) == 2
        self.metadata = metadata

    @staticmethod
    def from_metadata(
        line: str, raise_error: Callable[[str], ParseError]
    ) -> "Connection":
        match_ = re.fullmatch(r"connection\s*:\s*(\w+)-(\w+)(\s+(\[.*\]))?", line)
        if not match_:
            raise raise_error("broken connection definition")

        inline_metadata: dict[str, str] = {}
        if match_.group(4):
            inline_metadata = extract_inline_metadata(match_.group(4), raise_error)
        if match_.group(1) == match_.group(2):
            raise raise_error("zone connect to itself")
        return Connection((match_.group(1), match_.group(2)), **inline_metadata)

    def to_tuple(self) -> tuple[str, str]:
        zones: list[str] = list(self.zones)
        zones.sort()
        return zones[0], zones[1]

    def __repr__(self) -> str:
        return f"Connection('{', '.join(self.zones)}')"


class Zone:
    connections: list[Connection]

    def __init__(self, name: str, x: int, y: int, color: str = "", zone: str = "normal", max_drones: int = 1) -> None:
        self.name = name

        self.x = x
        self.y = y
        self.metadata = metadata
        self.connections = []

    def __str__(self) -> str:
        return f"Zone({self.name}: {self.x},{self.y})"

    def add_connection(self, connection: Connection) -> None:
        self.connections.append(connection)


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
            )

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

    lines: list[tuple[int, str]]
    number_of_drones: int
    zones: dict[str, Zone]

    def __init__(self, metadata: str, file_path: str) -> None:
        self.zones = {}

        self.file_path = file_path
        self._sanitize_lines(metadata.split("\n"))
        if self.lines == []:
            raise ParseError(0, "noting to extract, file empty")
        self.number_of_drones = self._nb_drones(self.lines[0])
        self.lines = self.lines[1:]
        self._extract_zones_and_conections()

    def _create_connection(
        self, line_num: int, line: str, connections: set[tuple[str, str]]
    ) -> None:
        connection = Connection.from_metadata(
            line, lambda msg: ParseError(line_num, msg)
        )

        zones = connection.to_tuple()
        if zones in connections:
            raise ParseError(line_num, "duplicated connection")
        if any(z not in self.zones for z in zones):
            raise ParseError(line_num, "connecting to non existsing zone")
        for z in zones:
            self.zones[z].add_connection(connection)

    def _extract_zones_and_conections(self) -> dict[str, Zone]:
        # these two `sets` below, is only for caching
        zp = self.ZoneParser()
        connections: set[tuple[str, str]] = set()

        for line_num, line in self.lines:
            if re.match(r"^(start_|end_)?hub\s*:", line):
                zone = zp.extract(line_num, line)
                self.zones[zone.name] = zone
            elif re.fullmatch(r"^connection\s*:.+", line):
                self._create_connection(line_num, line, connections)
            elif re.fullmatch(r"^nb_drones\s*:.+", line):
                raise ParseError(line_num, "re-assign `nb_drones`")
            elif re.match(r"^[\w\s]+\s*:.+", line):
                raise ParseError(
                    line_num, f"Unknown keyword `{line.split(':')[0].strip()}`"
                )
            else:
                raise ParseError(line_num, "broken line")
        return {}

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

        d = DataParser(metadata, PATH)
    except ParseError as e:
        print(e)
        exit()
    for z in d.zones.values():
        print(z)
        print(z.connections)
