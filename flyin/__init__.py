from .typs import Zone, Connection
from .parser import DataParser
from .gui import Visualizer
from raylib import SetTargetFPS

SetTargetFPS(60)

__all__ = (
    "Zone",
    "Connection",
    "DataParser",
    "Visualizer"
)
