from .typs import Zone, Connection, Drone, Point, Location
from .color import colors
from .parser import DataParser
from .engine import Engine
from .gui import Visualizer
from raylib import SetTargetFPS, SetTraceLogLevel, LOG_NONE

SetTraceLogLevel(LOG_NONE)
SetTargetFPS(60)

__all__ = (
    "Zone",
    "Engine",
    "Connection",
    "Point",
    "Location",
    "Drone",
    "DataParser",
    "Visualizer",
    "colors"
)
