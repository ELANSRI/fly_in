import pyglet
from pyglet import shapes
from models import NetworkMap
from typing import Dict, List, Tuple


class Visualizer(pyglet.window.Window):
    """Manages the window, map element rendering, and animation playback."""

    def __init__(self, network: NetworkMap, simulation_result: Dict[int, List[str]]) -> None:
        super().__init__(1000, 800, caption="Fly-in Simulator")
        self.network = network
        self.result = simulation_result
        self.coord_scale = 60
        self.offset_x = 100
        self.offset_y = 700

        self.render_nodes: List[shapes.Circle] = []
        self.render_edges: List[shapes.Line] = []

        self.animation_speed = 1.0
        self.animation_progress = 0.0
        self.current_turn = 0
        self.manual_mode = False
        self.max_turns = max((len(p) - 1 for p in simulation_result.values()), default=0)

        self.turn_label = pyglet.text.Label(
            text=f"Turn: 0 / {self.max_turns} (AUTO)",
            font_name="Arial", font_size=18, x=20, y=self.height - 30, color=(255, 255, 255, 255)
        )

        self.drone_shapes: Dict[int, shapes.Circle] = {
            d_id: shapes.Circle(0, 0, radius=10, color=(255, 255, 0))
            for d_id in simulation_result
        }

        self._setup_map_graphics()
        pyglet.clock.schedule_interval(self.update_timeline, 1 / 60.0)

    def _setup_map_graphics(self) -> None:
        """Generates line shapes for links and colored circles for zone hubs."""
        for link in self.network.connections:
            z1, z2 = list(link)
            zone1, zone2 = self.network.zones[z1], self.network.zones[z2]
            x1 = self.offset_x + (zone1.x * self.coord_scale)
            y1 = self.offset_y + (zone1.y * self.coord_scale)
            x2 = self.offset_x + (zone2.x * self.coord_scale)
            y2 = self.offset_y + (zone2.y * self.coord_scale)
            self.render_edges.append(shapes.Line(x1, y1, x2, y2, thickness=3, color=(100, 100, 100)))

        color_map = {"green": (46, 204, 113), "red": (255, 30, 30), "blue": (41, 128, 185), "yellow": (241, 196, 15)}
        for name, zone in self.network.zones.items():
            x = self.offset_x + (zone.x * self.coord_scale)
            y = self.offset_y + (zone.y * self.coord_scale)
            color = color_map.get(zone.color or "", (128, 128, 128)) if zone.color else (200, 200, 200)
            if name == self.network.start_hub: color = (0, 255, 0)
            if name == self.network.end_hub: color = (0, 0, 255)
            self.render_nodes.append(shapes.Circle(x, y, radius=15, color=color))

    def _get_drone_position(self, path: List[str], turn: int, progress: float) -> Tuple[float, float]:
        """Calculates interpolated screen coordinates for a drone."""
        turn_history = [p.split("-")[-1] for p in path]

        if turn >= len(turn_history) - 1:
            z = self.network.zones[turn_history[-1]]
            return float(self.offset_x + z.x * self.coord_scale), float(self.offset_y + z.y * self.coord_scale)

        z_curr = self.network.zones[turn_history[turn]]
        z_next = self.network.zones[turn_history[turn + 1]]
        x1 = self.offset_x + z_curr.x * self.coord_scale
        y1 = self.offset_y + z_curr.y * self.coord_scale
        x2 = self.offset_x + z_next.x * self.coord_scale
        y2 = self.offset_y + z_next.y * self.coord_scale
        return x1 + (x2 - x1) * progress, y1 + (y2 - y1) * progress

    def update_timeline(self, time_slice: float) -> None:
        """Advances animation progress and recalculates drone coordinates."""
        if not self.manual_mode:
            self.animation_progress += time_slice / self.animation_speed
            if self.animation_progress >= 1.0:
                self.animation_progress = 0.0
                self.current_turn = min(self.current_turn + 1, self.max_turns)
        else:
            self.animation_progress = 0.0

        mode_str = "MANUAL" if self.manual_mode else "AUTO"
        self.turn_label.text = f"Turn: {self.current_turn} / {self.max_turns} ({mode_str})"

        for d_id, path in self.result.items():
            dx, dy = self._get_drone_position(path, self.current_turn, self.animation_progress)
            self.drone_shapes[d_id].x = dx
            self.drone_shapes[d_id].y = dy

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        """Captures keyboard inputs to jump timelines or toggle states."""
        from pyglet.window import key
        if symbol == key.SPACE:
            self.manual_mode = not self.manual_mode
        elif symbol == key.RIGHT:
            self.manual_mode = True
            self.current_turn = min(self.current_turn + 1, self.max_turns)
        elif symbol == key.LEFT:
            self.manual_mode = True
            self.current_turn = max(self.current_turn - 1, 0)

    def on_draw(self) -> None:
        """Clears frame context buffer and issues render orders."""
        self.clear()
        for edge in self.render_edges: edge.draw()
        for node in self.render_nodes: node.draw()
        for drone in self.drone_shapes.values(): drone.draw()
        self.turn_label.draw()