from .typs import Zone, Connection, Drone, Point
from .color import colors
from .parser import DataParser
from .gui import Visualizer
from raylib import SetTargetFPS

SetTargetFPS(60)

__all__ = (
    "Zone",
    "Connection",
    "Point",
    "Drone",
    "DataParser",
    "Visualizer",
    "colors"
)
