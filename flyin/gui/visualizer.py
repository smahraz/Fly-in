from os import wait
from raylib import *
from flyin import DataParser

BG_COLOR = (0x66, 0x33, 0x99, 0xff)

WIDTH = 1200
HEIGHT = 800

SIDEPANEL_BG_COLOR = (0x4c, 0x4e, 0x96, 0xff)
SIDEPANEL_WIDTH = 250
SIDEPANEL_HEIGHT = HEIGHT


ZONE_RADIUS = 50.0
SCALE = int(ZONE_RADIUS)
ZONE_SPACING = SCALE + 40

TITLE = b"Fly-in"


class SidePanel:
    def __init__(self, parsing_data: DataParser) -> None:
        self.parsing_data = parsing_data
        self.y = 0
        self.x = WIDTH - SIDEPANEL_WIDTH

    def draw(self) -> None:
        DrawRectangle(
            self.x,
            self.y,
            SIDEPANEL_WIDTH,
            SIDEPANEL_HEIGHT,
            SIDEPANEL_BG_COLOR
        )
        self._draw_textwidget1(
            "Number of Drones:",
            f"{self.parsing_data.number_of_drones}"
        )

    def _draw_textwidget1(self, title: str, value: str) -> None:
        TITLE_TEXT_SIZE = 17
        VALUE_TEXT_SIZE = 15
        self.y += 20
        x = self.x + 12

        DrawText(
            title.encode(),
            x,
            self.y,
            TITLE_TEXT_SIZE,
            WHITE
        )
        self.y += 20
        x += 20
        DrawText(
            value.encode(),
            x,
            self.y,
            VALUE_TEXT_SIZE,
            WHITE
        )


class Visualizer:

    def __init__(self, parsing_data: DataParser) -> None:
        self.parsing_data = parsing_data
        self._init_camera()

    @classmethod
    def start(cls, parsing_data: DataParser) -> None:
        InitWindow(WIDTH, HEIGHT, TITLE)
        cls(parsing_data).loop()
        CloseWindow()

    def loop(self) -> None:
        while not WindowShouldClose():
            wheel = GetMouseWheelMove()
            if wheel:
                self._mouse_wheel(wheel)
            if IsMouseButtonDown(MOUSE_BUTTON_LEFT):
                self._mouse_drag()

            ClearBackground(BG_COLOR)
            BeginDrawing()
            BeginMode2D(self._camera[0])
            self._draw_connections()
            self._draw_zones()
            EndMode2D()
            self._draw_sidepanel()
            EndDrawing()

    def _draw_sidepanel(self) -> None:
        SidePanel(self.parsing_data).draw()

    def _draw_zones(self) -> None:
        FONT_SIZE = 18
        for zone in self.parsing_data.zones.values():
            x, y = self._scaling_formula(zone.x, zone.y)
            DrawCircle(
                x, y,
                ZONE_RADIUS,
                zone.color
            )
            font_width = MeasureText(zone.name.encode(), FONT_SIZE)
            if font_width > SCALE * 2 + 30 and zone.x % 2:
                y += SCALE + 3
                print("here")
            else:
                y -= SCALE + 18

            DrawText(
                zone.name.encode(),
                x - font_width // 2,
                y,
                FONT_SIZE,
                WHITE
            )



    def _draw_connections(self) -> None:
        def z2p(obj: Visualizer, zone_name: str) -> tuple[int, int]:
            zone = obj.parsing_data.zones[zone_name]
            return zone.x, zone.y
        drawn_conn = set()
        for zone in self.parsing_data.zones.values():
            for conn in zone.connections:
                if conn in drawn_conn:
                    continue
                drawn_conn.add(conn)
                z1, z2 = conn.zones
                DrawLine(
                    *self._scaling_formula(*z2p(self, z1)),
                    *self._scaling_formula(*z2p(self, z2)),
                    BLACK
                )

    def _mouse_wheel(self, wheel_move: float) -> None:
        if self._camera.zoom < 2:
            self._camera.zoom += wheel_move * 0.05
            if self._camera.zoom < 0.2:
                self._camera.zoom = 0.2
        else:
            self._camera.zoom += wheel_move * 0.4

    def _mouse_drag(self) -> None:
        delta = GetMouseDelta()
        self._camera.target.x -= delta.x / self._camera.zoom
        self._camera.target.y -= delta.y / self._camera.zoom

    @staticmethod
    def _scaling_formula(x: int, y: int) -> tuple[int, int]:
        x = x * SCALE + x * ZONE_SPACING
        y = y * SCALE + y * ZONE_SPACING
        return x, y

    def _init_camera(self) -> None:
        self._camera = ffi.new("Camera2D *")
        self._camera.offset.x = 70
        self._camera.offset.y = HEIGHT // 2
        self._camera.target.x = 0
        self._camera.target.y = 0
        self._camera.rotation = 0
        self._camera.zoom = 1
