import raylib as rl
from flyin import Zone, DataParser, Point, Drone
from flyin.parser import SCALE
from flyin import Engine

BG_COLOR = (0x66, 0x33, 0x99, 0xff)

WIDTH = 1200
HEIGHT = 800

SIDEPANEL_BG_COLOR = (0x4c, 0x4e, 0x96, 0xff)
SIDEPANEL_WIDTH = 250
SIDEPANEL_HEIGHT = HEIGHT

PAUSE_TIME = 1.0

ZONE_RADIUS = 50.0

ZONE_SPACING = SCALE + 40

TITLE = b"Fly-in"


class SidePanel:
    def __init__(self, parsing_data: DataParser) -> None:
        self.parsing_data = parsing_data
        self.y = 0
        self.x = WIDTH - SIDEPANEL_WIDTH

    def draw(self) -> None:
        rl.DrawRectangle(
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

        rl.DrawText(
            title.encode(),
            x,
            self.y,
            TITLE_TEXT_SIZE,
            rl.WHITE
        )
        self.y += 20
        x += 20
        rl.DrawText(
            value.encode(),
            x,
            self.y,
            VALUE_TEXT_SIZE,
            rl.WHITE
        )


class DrawDrone:
    TRAVEL_TIME = 1

    all_poses: dict[Drone, Point] = {}

    def __init__(self, drone: Drone, dt: float) -> None:
        self.drone = drone
        self.dt = dt

    def draw(self) -> bool:
        v = self.speed(self.drone)
        if v == 0:
            self.all_poses[self.drone] = self.drone.prev_location.pos.cp()
            self._draw_drone()
            return True

        if self.drone not in self.all_poses:
            self.all_poses[self.drone] = self.drone.prev_location.pos.cp()
            self._draw_drone()
            return False

        remaining = self.all_poses[self.drone].distance(
                self.drone.current_location.pos
        )

        if remaining < 1.5:
            self.all_poses[self.drone] = self.drone.current_location.pos.cp()
            self._draw_drone()
            return True

        delta = self.drone.current_location.pos - self.all_poses[self.drone]

        pos = self.all_poses[self.drone]

        pos.x += (delta.x / remaining) * v * self.dt
        pos.y += (delta.y / remaining) * v * self.dt

        self._draw_drone()

        return False

    @staticmethod
    def speed(d: Drone) -> float:
        return d.prev_location.pos.distance(d.current_location.pos) \
            / DrawDrone.TRAVEL_TIME

    def _draw_drone(self) -> None:
        rl.DrawCircle(
            *self.all_poses[self.drone].as_tuple(),
            25.0,
            rl.WHITE
        )
        rl.DrawText(
            f"{self.drone.drone_id}".encode(),
            *self.all_poses[self.drone].as_tuple(),
            50,
            rl.BLACK
        )


class Visualizer:

    def __init__(self, parsing_data: DataParser) -> None:
        self.parsing_data = parsing_data
        self.simulation = Engine(parsing_data).simulation()
        self.drones = next(self.simulation)
        self._init_camera()

    @classmethod
    def start(cls, parsing_data: DataParser) -> None:
        rl.InitWindow(WIDTH, HEIGHT, TITLE)
        cls(parsing_data).loop()
        rl.CloseWindow()

    def loop(self) -> None:
        pause_time = 0.0
        while not rl.WindowShouldClose():
            wheel = rl.GetMouseWheelMove()
            if wheel:
                self._mouse_wheel(wheel)
            if rl.IsMouseButtonDown(rl.MOUSE_BUTTON_LEFT):
                self._mouse_drag()

            rl.ClearBackground(BG_COLOR)
            rl.BeginDrawing()
            rl.BeginMode2D(self._camera[0])
            self._draw_connections()
            self._draw_zones()
            if self._draw_drones():
                if pause_time > PAUSE_TIME:
                    pause_time = 0
                    next(self.simulation)
                else:
                    pause_time += rl.GetFrameTime()
            rl.EndMode2D()
            self._draw_sidepanel()
            rl.EndDrawing()

    def _draw_drones(self) -> bool:
        next_ = True
        dt = rl.GetFrameTime()
        for d in self.drones:
            next_ &= DrawDrone(d, dt).draw()
        return next_

    def _draw_sidepanel(self) -> None:
        SidePanel(self.parsing_data).draw()

    def _draw_zones(self) -> None:
        FONT_SIZE = 18
        for zone in self.parsing_data.zones.values():
            mergin = 0
            if zone.zone is Zone.ZoneType.RESTRICTED:
                mergin = 10
                factor = 0.5
                darker_color = (
                    int(zone.color[0] * factor),
                    int(zone.color[1] * factor),
                    int(zone.color[2] * factor),
                    0xff
                )

                rl.DrawCircle(
                    *zone.pos.as_tuple(),
                    ZONE_RADIUS,
                    darker_color
                )

            rl.DrawCircle(
                *zone.pos.as_tuple(),
                ZONE_RADIUS - mergin,
                zone.color
            )

            font_width = rl.MeasureText(zone.name.encode(), FONT_SIZE)
            y = zone.pos.y
            if font_width > SCALE / 1.2 and (zone.pos.x // SCALE) % 2:
                y += ZONE_RADIUS + 3
            else:
                y -= ZONE_RADIUS + 18

            rl.DrawText(
                zone.name.encode(),
                int(zone.pos.x) - font_width // 2,
                int(y),
                FONT_SIZE,
                rl.WHITE
            )

    def _draw_connections(self) -> None:
        drawn_conn = set()
        for zone in self.parsing_data.zones.values():
            for conn in zone.connections:
                if conn in drawn_conn:
                    continue
                drawn_conn.add(conn)
                z1, z2 = conn.zones
                color = rl.BLACK
                if any(z.zone is Zone.ZoneType.RESTRICTED for z in conn.zones):
                    color = rl.RED

                rl.DrawLine(
                    *z1.pos.as_tuple(),
                    *z2.pos.as_tuple(),
                    color
                )

    def _mouse_wheel(self, wheel_move: float) -> None:
        if self._camera.zoom < 2:
            self._camera.zoom += wheel_move * 0.05
            if self._camera.zoom < 0.2:
                self._camera.zoom = 0.2
        else:
            self._camera.zoom += wheel_move * 0.4

    def _mouse_drag(self) -> None:
        delta = rl.GetMouseDelta()
        self._camera.target.x -= delta.x / self._camera.zoom
        self._camera.target.y -= delta.y / self._camera.zoom

    def _init_camera(self) -> None:
        self._camera = rl.ffi.new("Camera2D *")
        self._camera.offset.x = 70
        self._camera.offset.y = HEIGHT // 2
        self._camera.target.x = 0
        self._camera.target.y = 0
        self._camera.rotation = 0
        self._camera.zoom = 1
