from raylib import *
from ._consts import *


class Visualizer:
    @classmethod
    def start(cls) -> None:
        InitWindow(WIDTH, HEIGHT, TITLE)
        cls().loop()
        CloseWindow()

    def loop(self) -> None:
        while not WindowShouldClose():
            ClearBackground(BG_COLOR)
            BeginDrawing()
            EndDrawing()
