from flyin import Visualizer, DataParser
from sys import argv


map_path = argv[1]


with open(map_path, "r") as mp_file:
    dp = DataParser(mp_file.read())

Visualizer.start(dp)
