from flyin import Visualizer, DataParser
from sys import argv
from .exceptions import ParseError, MapError


def try_read_file(file_path: str) -> str:
    try:
        with open(file_path, "r") as mp_file:
            return mp_file.read()
    except BaseException as e:
        print(f"Error: {e}")
        exit(1)


if len(argv) != 2:
    print("Usage: python main.py <map_path>")
    exit()

map_path = argv[1]

try:
    dp = DataParser(try_read_file(map_path))
    Visualizer.start(dp)
except ParseError as e:
    print(f"ParseError: {e}")
except MapError:
    print("Error: There is no path between start_hub and end_hub")
