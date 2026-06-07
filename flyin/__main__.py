from flyin import Visualizer
from flyin import DataParser


MAP_PATH = "maps/challenger/01_the_impossible_dream.txt"


with open(MAP_PATH, "r") as mp_file:
    dp = DataParser(mp_file.read())

Visualizer.start(dp)
