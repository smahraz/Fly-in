import re
from typing import Callable


class ParseError(Exception):
    def __init__(self, file_path: str, line_number: int, msg: str) -> None:
        self.file_path = file_path
        self.line_number = line_number
        self.msg = msg
        super().__init__(f"{file_path}:{line_number}: {msg}")


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


class Zone:

    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        metadata: dict[str, str]
    ) -> None:
        self.name = name

        self.x = x
        self.y = y
        self.metadata = metadata

    def __str__(self) -> str:
        return f"Zone({self.name}: {self.x},{self.y})"

    @staticmethod
    def from_metadata(
        line: str,
        raise_error: Callable[[str], ParseError]
    ) -> "Zone":
        inline_metadata: dict[str, str] = {}
        match_ = re.fullmatch(
            r"[a-z_]+\s*:\s*(\w+)\s+(\d+)\s+(\d+)(\s+(\[.*\]))?", line
        )
        if not match_:
            raise raise_error("broken zone metadata")
        if match_.group(5):
            inline_metadata = extract_inline_metadata(
                match_.group(5),
                raise_error
            )
        inline_metadata["-type"] = line.split(":")[0].strip()
        return Zone(
            match_.group(1),
            int(match_.group(2)),
            int(match_.group(3)),
            inline_metadata,
        )


class DataParser:

    lines: list[tuple[int, str]]
    number_of_drones: int
    zones: dict[str, Zone]

    def __init__(self, metadata: str, file_path: str) -> None:
        self.zones = {}

        self.file_path = file_path
        self._sanitize_lines(metadata.split("\n"))
        if self.lines == []:
            raise ParseError(file_path, 0, "file is empty of date")
        self.number_of_drones = self._nb_drones(self.lines[0])
        self.lines = self.lines[1:]
        self.zone = self._extract_zones_conection()

    def _add_zone(
        self, line_num: int, line: str, coordinate: set[tuple[int, int]]
    ) -> None:
        zone = Zone.from_metadata(
            line,
            lambda msg: self._raise_error(line_num, msg)
        )
        if zone.name in self.zones:
            raise self._raise_error(
                line_num,
                f"duplicated zone name '{zone.name}'"
            )
        if (zone.x, zone.y) in coordinate:
            raise self._raise_error(line_num, "two zones collapse")
        self.zones[zone.name] = zone
        coordinate.add((zone.x, zone.y))

    def _extract_zones_conection(self) -> dict[str, Zone]:
        coordinate: set[tuple[int, int]] = set()
        for line_num, line in self.lines:
            if re.fullmatch(r"^(start_hub|end_hub|hub)\s*:.+", line):
                self._add_zone(line_num, line, coordinate)
            elif re.fullmatch(r"^connection\s*:.+", line):
                pass
            elif re.fullmatch(r"^nb_drones\s*:.+", line):
                raise self._raise_error(line_num, "re-assign `nb_drones`")
            elif re.match(r"^[\w]+\s*:.+", line):
                raise self._raise_error(
                    line_num, f"wrong keyword `{line.split(':')[0].strip()}`"
                )
            else:
                raise self._raise_error(line_num, "broken line")
        return {}

    def _nb_drones(self, line: tuple[int, str]) -> int:
        if not re.match(r"^nb_drones\s*:", line[1]):
            raise self._raise_error(0, "missing first key `nb_drones`")
        match_ = re.fullmatch(r"nb_drones\s*:\s*[+-]?(\d+)", line[1])
        if match_ is None:
            raise self._raise_error(line[0], "Wrong format for `nb_drones`")
        number = int(match_.group(1))
        if number <= 0:
            raise self._raise_error(line[0], "`nb_drones` <= 0")
        return number

    def _sanitize_lines(self, lines: list[str]) -> None:
        self.lines: list[tuple[int, str]] = []
        for line_num, line in enumerate(lines, start=1):
            line = line.split("#")[0].strip()
            if line:
                self.lines.append((line_num, line))

    def _raise_error(self, line_num: int, msg: str) -> ParseError:
        return ParseError(self.file_path, line_num, msg)


if __name__ == "__main__":
    PATH = "maps/easy/01_linear_path.txt"
    with open(PATH, "r") as file:
        metadata = file.read()

    d = DataParser(metadata, PATH)
