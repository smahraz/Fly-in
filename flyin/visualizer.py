import raylib as rl
from flyin import Zone, DataParser, Point, Drone
from flyin.parser import SCALE
from flyin import Engine


BG_COLOR = rl.GRAY

WIDTH = 1200
HEIGHT = 800

PAUSE_TIME = 0.3

ZONE_RADIUS = 50.0

ZONE_SPACING = SCALE + 40

TITLE = b"Fly-in"


class DrawInfo:
    def __init__(
        self,
        parsing_data: DataParser,
        turn: int,
        zoom: float
    ) -> None:
        self.parsing_data = parsing_data
        self.turn = turn
        self.zoom = zoom
        self.y = 10
        self.x = 20

    def draw(self) -> None:
        self._draw_textwidget(
            "Drones: "
            f"{self.parsing_data.end_hub.drone_count}"
            f"/{self.parsing_data.number_of_drones}"
        )
        self._draw_textwidget(f"Turn: {self.turn}")
        self._draw_textwidget(f"Zoom: {self.zoom:.2}x")

    def _draw_textwidget(self, title: str) -> None:
        TITLE_TEXT_SIZE = 20

        rl.DrawText(
            title.encode(),
            self.x,
            self.y,
            TITLE_TEXT_SIZE,
            rl.WHITE
        )
        self.y += 20


class DrawButtons:
    def __init__(self, pause_simulation: bool) -> None:
        self.textures = [
            rl.LoadTexture(b"assets/space.png"),
            rl.LoadTexture(b"assets/r.png"),
            rl.LoadTexture(b"assets/enter.png")
        ]
        self.pause_simulation = pause_simulation
        self.x = 5
        self.y = HEIGHT - 24

    def draw(self) -> None:
        self._draw_button(
            0,
            "Start" if self.pause_simulation else "Pause",
        )
        self._draw_button(1, "Reset")
        self._draw_button(2, "Skip")

    def _draw_button(self, texture_index: int, text: str) -> None:
        texture = self.textures[texture_index]
        rl.DrawTextureEx(
            texture,
            (self.x, self.y),
            0,
            0.5,
            rl.WHITE
        )
        rl.DrawText(
            text.encode(),
            self.x + int(texture.width * 0.5) + 5,
            self.y,
            texture.height // 2,
            rl.WHITE,
        )
        self.x += rl.MeasureText(text.encode(), texture.height // 2) + 20
        self.x += texture.width // 2


class DrawDrone:
    TRAVEL_TIME = 0.4

    all_poses: dict[Drone, Point] = {}

    def __init__(self, drone: Drone, dt: float, no_animation: bool) -> None:
        self.drone = drone
        self.dt = dt
        self.no_animation = no_animation

    def draw(self) -> bool:
        if self.no_animation:
            self._draw_drone()
            return False

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

        # quick fix: if drone surpasses the destination, set it in the destination and end animation.
        if pos.distance(self.drone.prev_location.pos) > self.drone.current_location.pos.distance(self.drone.prev_location.pos):
            self.all_poses[self.drone] = self.drone.current_location.pos.cp()
            self._draw_drone()
            return True

        self._draw_drone()

        return False

    @staticmethod
    def speed(d: Drone) -> float:
        return d.prev_location.pos.distance(d.current_location.pos) \
            / DrawDrone.TRAVEL_TIME

    def _draw_drone(self) -> None:
        rl.DrawCircle(
            *self.all_poses[self.drone].as_tuple(),
            30.0,
            rl.WHITE
        )
        x, y = self.all_poses[self.drone].as_tuple()
        text_width = rl.MeasureText(f"{self.drone.drone_id}".encode(), 50)
        rl.DrawText(
            f"{self.drone.drone_id}".encode(),
            x - text_width // 2,
            y - 22,
            50,
            rl.BLACK
        )


class Visualizer:

    def __init__(self, parsing_data: DataParser) -> None:
        self.parsing_data = parsing_data
        self.simulation = Engine(parsing_data).simulation()
        self.drones = next(self.simulation)
        self._init_camera()
        self.pause_simulation = False

    @classmethod
    def start(cls, parsing_data: DataParser) -> None:
        rl.InitWindow(WIDTH, HEIGHT, TITLE)
        cls(parsing_data).loop()
        rl.CloseWindow()

    def loop(self) -> None:
        pause_time = 0.0
        self.turn = 0
        while not rl.WindowShouldClose():
            wheel = rl.GetMouseWheelMove()
            if wheel:
                self._mouse_wheel(wheel)
            if rl.IsMouseButtonDown(rl.MOUSE_BUTTON_LEFT):
                self._mouse_drag()

            self.check_keyinputs()

            rl.ClearBackground(BG_COLOR)
            rl.BeginDrawing()
            rl.BeginMode2D(self._camera[0])
            self._draw_connections()
            self._draw_zones()
            if self._draw_drones():
                if pause_time > PAUSE_TIME:
                    pause_time = 0
                    try:
                        print(" ".join(str(d) for d in next(self.simulation)))
                        self.turn += 1
                    except StopIteration:
                        self.pause_simulation = True
                else:
                    pause_time += rl.GetFrameTime()
            rl.EndMode2D()
            DrawInfo(self.parsing_data, self.turn, self._camera.zoom).draw()
            DrawButtons(self.pause_simulation).draw()
            rl.EndDrawing()

    def check_keyinputs(self) -> None:
        if rl.IsKeyPressed(rl.KEY_SPACE):
            self.pause_simulation = not self.pause_simulation
        if rl.IsKeyPressed(rl.KEY_R):
            self.pause_simulation = False
            self.simulation = Engine(self.parsing_data).simulation()
            for z in self.parsing_data.zones.values():
                z.drone_count = 0
            Drone.drone_id = 0
            self.drones = next(self.simulation)
            self.turn = 0
        if rl.IsKeyPressed(rl.KEY_ENTER):
            turn = 0
            for moves in self.simulation:
                turn += 1
                print(" ".join(str(d) for d in moves))
            DrawDrone.all_poses = {}
            self.turn += turn
            for d in self.drones:
                d.prev_location = d.current_location

    def _draw_drones(self) -> bool:
        next_ = True
        dt = rl.GetFrameTime()
        for d in self.drones:
            next_ &= DrawDrone(d, dt, self.pause_simulation).draw()
        if self.pause_simulation:
            return False
        return next_

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
            rl.DrawText(
                f"[{zone.drone_count}/{zone.max_drones}]".encode(),
                int(zone.pos.x + ZONE_RADIUS / 2),
                int(zone.pos.y + ZONE_RADIUS / 2),
                FONT_SIZE - 2,
                rl.WHITE,
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
