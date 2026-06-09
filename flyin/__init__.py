from .typs import Zone, Connection, Drone
from .color import colors
from .parser import DataParser
from .gui import Visualizer
from raylib import SetTargetFPS

SetTargetFPS(60)

__all__ = (
    "Zone",
    "Connection",
    "Drone",
    "DataParser",
    "Visualizer",
    "colors"
)
