from __future__ import annotations

import math

import pygame


WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
TOOLBAR_HEIGHT = 110

CANVAS_WIDTH = WINDOW_WIDTH
CANVAS_HEIGHT = WINDOW_HEIGHT - TOOLBAR_HEIGHT


class PaintApp:
    """Practice 11 paint app with more geometric shapes."""

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Practice 11 - Paint")

        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 17, bold=True)

        # Canvas stores final drawings.
        self.canvas = pygame.Surface((CANVAS_WIDTH, CANVAS_HEIGHT))
        self.canvas.fill((255, 255, 255))

        self.tools: list[tuple[str, pygame.Rect]] = []
        self.colors: list[tuple[tuple[int, int, int], pygame.Rect]] = []
        self.build_toolbar()

        self.current_tool = "pen"
        self.current_color = (0, 0, 0)

        self.pen_size = 4
        self.eraser_size = 22
        self.shape_border_width = 3

        # Drawn objects are saved as shape dictionaries.
        self.shapes: list[dict[str, object]] = []
        self.erase_strokes: list[dict[str, object]] = []

        self.is_drawing = False
        self.start_pos: tuple[int, int] | None = None
        self.current_pos: tuple[int, int] | None = None
        self.active_stroke_points: list[tuple[int, int]] = []

        self.pen_cursor, self.pen_hotspot = self.create_pen_cursor_icon()
        self.eraser_cursor, self.eraser_hotspot = self.create_eraser_cursor_icon()
        pygame.mouse.set_visible(False)

    def build_toolbar(self) -> None:
        tool_names = [
            "pen",
            "rectangle",
            "circle",
            "square",
            "right_triangle",
            "equilateral_triangle",
            "rhombus",
            "eraser",
        ]

        # 2 rows x 4 columns buttons.
        x0 = 12
        y0 = 10
        w = 145
        h = 34
        gap_x = 8
        gap_y = 6

        for index, name in enumerate(tool_names):
            row = index // 4
            col = index % 4
            x = x0 + col * (w + gap_x)
            y = y0 + row * (h + gap_y)
            self.tools.append((name, pygame.Rect(x, y, w, h)))

        palette = [
            (0, 0, 0),
            (255, 0, 0),
            (0, 120, 255),
            (40, 170, 70),
            (255, 180, 0),
            (170, 65, 225),
            (120, 120, 120),
            (255, 255, 255),
        ]

        color_x = 640
        color_y = 18
        color_size = 26
        for color in palette:
            self.colors.append((color, pygame.Rect(color_x, color_y, color_size, color_size)))
            color_x += color_size + 8

    def get_canvas_pos(self, screen_pos: tuple[int, int]) -> tuple[int, int] | None:
        sx, sy = screen_pos
        cy = sy - TOOLBAR_HEIGHT
        if 0 <= sx < CANVAS_WIDTH and 0 <= cy < CANVAS_HEIGHT:
            return (sx, cy)
        return None

    def create_pen_cursor_icon(self) -> tuple[pygame.Surface, tuple[int, int]]:
        surface = pygame.Surface((26, 26), pygame.SRCALPHA)
        pygame.draw.polygon(surface, (60, 70, 85), [(5, 3), (21, 19), (16, 24), (0, 8)])
        pygame.draw.polygon(surface, (120, 136, 154), [(7, 4), (17, 14), (14, 17), (4, 7)])
        pygame.draw.polygon(surface, (236, 216, 175), [(16, 24), (22, 18), (24, 20), (18, 26)])
        pygame.draw.polygon(surface, (40, 40, 40), [(20, 22), (24, 20), (22, 24)])
        return surface, (20, 22)

    def create_eraser_cursor_icon(self) -> tuple[pygame.Surface, tuple[int, int]]:
        surface = pygame.Surface((26, 26), pygame.SRCALPHA)
        pygame.draw.rect(surface, (245, 127, 151), (4, 6, 18, 14), border_radius=4)
        pygame.draw.rect(surface, (255, 255, 255), (4, 6, 9, 14), border_radius=4)
        pygame.draw.rect(surface, (95, 95, 100), (4, 6, 18, 14), width=2, border_radius=4)
        return surface, (13, 13)

    def get_drag_rect(self, start: tuple[int, int], end: tuple[int, int]) -> pygame.Rect:
        left = min(start[0], end[0])
        top = min(start[1], end[1])
        width = abs(start[0] - end[0])
        height = abs(start[1] - end[1])
        return pygame.Rect(left, top, width, height)

    def get_square_rect(self, start: tuple[int, int], end: tuple[int, int]) -> pygame.Rect | None:
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        side = min(abs(dx), abs(dy))
        if side <= 0:
            return None

        x = start[0] if dx >= 0 else start[0] - side
        y = start[1] if dy >= 0 else start[1] - side
        return pygame.Rect(x, y, side, side)

    def get_right_triangle_points(self, start: tuple[int, int], end: tuple[int, int]) -> list[tuple[int, int]]:
        rect = self.get_drag_rect(start, end)
        if rect.width <= 0 or rect.height <= 0:
            return []
        return [
            (rect.left, rect.bottom),
            (rect.left, rect.top),
            (rect.right, rect.bottom),
        ]

    def get_equilateral_triangle_points(
        self,
        start: tuple[int, int],
        end: tuple[int, int],
    ) -> list[tuple[int, int]]:
        rect = self.get_drag_rect(start, end)
        if rect.width <= 0 or rect.height <= 0:
            return []

        side = rect.width
        eq_height = int((math.sqrt(3) / 2) * side)
        if eq_height > rect.height:
            side = max(2, int(rect.height / (math.sqrt(3) / 2)))
            eq_height = int((math.sqrt(3) / 2) * side)

        center_x = rect.centerx
        top_y = rect.top + (rect.height - eq_height) // 2
        base_y = top_y + eq_height
        left_x = center_x - side // 2
        right_x = center_x + side // 2

        return [
            (center_x, top_y),
            (left_x, base_y),
            (right_x, base_y),
        ]

    def get_rhombus_points(self, start: tuple[int, int], end: tuple[int, int]) -> list[tuple[int, int]]:
        rect = self.get_drag_rect(start, end)
        if rect.width <= 0 or rect.height <= 0:
            return []
        return [
            (rect.centerx, rect.top),
            (rect.right, rect.centery),
            (rect.centerx, rect.bottom),
            (rect.left, rect.centery),
        ]

    def points_bounding_rect(self, points: list[tuple[int, int]]) -> pygame.Rect:
        min_x = min(point[0] for point in points)
        min_y = min(point[1] for point in points)
        max_x = max(point[0] for point in points)
        max_y = max(point[1] for point in points)
        return pygame.Rect(min_x, min_y, max_x - min_x, max_y - min_y)

    def draw_shape(self, surface: pygame.Surface, shape: dict[str, object]) -> None:
        shape_type = str(shape["type"])

        if shape_type == "stroke":
            points = list(shape["points"])  # type: ignore[arg-type]
            color = tuple(shape["color"])  # type: ignore[arg-type]
            width = int(shape["width"])
            if len(points) <= 1:
                pygame.draw.circle(surface, color, points[0], max(1, width // 2))
            else:
                pygame.draw.lines(surface, color, False, points, width)
            return

        if shape_type in {"rectangle", "circle", "square"}:
            rect = pygame.Rect(shape["rect"])  # type: ignore[arg-type]
            color = tuple(shape["color"])  # type: ignore[arg-type]
            width = int(shape["width"])

            if shape_type in {"rectangle", "square"}:
                pygame.draw.rect(surface, color, rect, width=width)
            else:
                pygame.draw.ellipse(surface, color, rect, width=width)
            return

        if shape_type in {"right_triangle", "equilateral_triangle", "rhombus"}:
            points = list(shape["points"])  # type: ignore[arg-type]
            color = tuple(shape["color"])  # type: ignore[arg-type]
            width = int(shape["width"])
            pygame.draw.polygon(surface, color, points, width=width)

    def rebuild_canvas(self) -> None:
        self.canvas.fill((255, 255, 255))
        for shape in self.shapes:
            self.draw_shape(self.canvas, shape)
        for erase_stroke in self.erase_strokes:
            self.draw_shape(self.canvas, erase_stroke)

    def point_to_segment_distance(
        self,
        point: tuple[int, int],
        a: tuple[int, int],
        b: tuple[int, int],
    ) -> float:
        px, py = point
        ax, ay = a
        bx, by = b

        abx = bx - ax
        aby = by - ay
        apx = px - ax
        apy = py - ay

        ab_len_sq = abx * abx + aby * aby
        if ab_len_sq == 0:
            return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5

        t = (apx * abx + apy * aby) / ab_len_sq
        t = max(0.0, min(1.0, t))

        closest_x = ax + t * abx
        closest_y = ay + t * aby
        return ((px - closest_x) ** 2 + (py - closest_y) ** 2) ** 0.5

    def point_hits_shape(self, point: tuple[int, int], shape: dict[str, object]) -> bool:
        shape_type = str(shape["type"])

        if shape_type == "stroke":
            points = list(shape["points"])  # type: ignore[arg-type]
            width = int(shape["width"])
            threshold = max(6, width + 3)

            if len(points) == 1:
                dx = point[0] - points[0][0]
                dy = point[1] - points[0][1]
                return (dx * dx + dy * dy) <= threshold * threshold

            for index in range(len(points) - 1):
                dist = self.point_to_segment_distance(point, points[index], points[index + 1])
                if dist <= threshold:
                    return True
            return False

        if shape_type in {"rectangle", "circle", "square"}:
            rect = pygame.Rect(shape["rect"])  # type: ignore[arg-type]
            return rect.inflate(8, 8).collidepoint(point)

        if shape_type in {"right_triangle", "equilateral_triangle", "rhombus"}:
            points = list(shape["points"])  # type: ignore[arg-type]
            return self.points_bounding_rect(points).inflate(8, 8).collidepoint(point)

        return False

    def get_shape_index_at_point(self, point: tuple[int, int]) -> int:
        for index in range(len(self.shapes) - 1, -1, -1):
            if self.point_hits_shape(point, self.shapes[index]):
                return index
        return -1

    def delete_shape_at_point(self, point: tuple[int, int]) -> bool:
        index = self.get_shape_index_at_point(point)
        if index == -1:
            return False
        del self.shapes[index]
        self.rebuild_canvas()
        return True

    def handle_left_mouse_down(self, pos: tuple[int, int]) -> None:
        for tool_name, rect in self.tools:
            if rect.collidepoint(pos):
                self.current_tool = tool_name
                return

        for color, rect in self.colors:
            if rect.collidepoint(pos):
                self.current_color = color
                return

        canvas_pos = self.get_canvas_pos(pos)
        if canvas_pos is None:
            return

        self.is_drawing = True
        self.start_pos = canvas_pos
        self.current_pos = canvas_pos

        if self.current_tool in {"pen", "eraser"}:
            self.active_stroke_points = [canvas_pos]

    def handle_mouse_motion(self, pos: tuple[int, int]) -> None:
        if not self.is_drawing:
            return

        canvas_pos = self.get_canvas_pos(pos)
        if canvas_pos is None:
            return

        self.current_pos = canvas_pos

        if self.current_tool in {"pen", "eraser"}:
            if not self.active_stroke_points or self.active_stroke_points[-1] != canvas_pos:
                self.active_stroke_points.append(canvas_pos)

    def handle_right_mouse_down(self, pos: tuple[int, int]) -> None:
        # Right-click deletes one full shape.
        canvas_pos = self.get_canvas_pos(pos)
        if canvas_pos is None:
            return
        self.delete_shape_at_point(canvas_pos)

    def handle_left_mouse_up(self, pos: tuple[int, int]) -> None:
        if not self.is_drawing:
            return

        end_pos = self.get_canvas_pos(pos)
        if end_pos is None:
            end_pos = self.current_pos

        if self.start_pos is not None and end_pos is not None:
            if self.current_tool == "pen":
                if self.active_stroke_points:
                    self.shapes.append(
                        {
                            "type": "stroke",
                            "points": list(self.active_stroke_points),
                            "color": self.current_color,
                            "width": self.pen_size,
                        }
                    )
                    self.rebuild_canvas()

            elif self.current_tool == "eraser":
                if self.active_stroke_points:
                    self.erase_strokes.append(
                        {
                            "type": "stroke",
                            "points": list(self.active_stroke_points),
                            "color": (255, 255, 255),
                            "width": self.eraser_size,
                        }
                    )
                    self.rebuild_canvas()

            elif self.current_tool == "rectangle":
                rect = self.get_drag_rect(self.start_pos, end_pos)
                if rect.width > 0 and rect.height > 0:
                    self.shapes.append(
                        {
                            "type": "rectangle",
                            "rect": rect,
                            "color": self.current_color,
                            "width": self.shape_border_width,
                        }
                    )
                    self.rebuild_canvas()

            elif self.current_tool == "circle":
                rect = self.get_drag_rect(self.start_pos, end_pos)
                if rect.width > 0 and rect.height > 0:
                    self.shapes.append(
                        {
                            "type": "circle",
                            "rect": rect,
                            "color": self.current_color,
                            "width": self.shape_border_width,
                        }
                    )
                    self.rebuild_canvas()

            elif self.current_tool == "square":
                square_rect = self.get_square_rect(self.start_pos, end_pos)
                if square_rect is not None:
                    self.shapes.append(
                        {
                            "type": "square",
                            "rect": square_rect,
                            "color": self.current_color,
                            "width": self.shape_border_width,
                        }
                    )
                    self.rebuild_canvas()

            elif self.current_tool == "right_triangle":
                points = self.get_right_triangle_points(self.start_pos, end_pos)
                if points:
                    self.shapes.append(
                        {
                            "type": "right_triangle",
                            "points": points,
                            "color": self.current_color,
                            "width": self.shape_border_width,
                        }
                    )
                    self.rebuild_canvas()

            elif self.current_tool == "equilateral_triangle":
                points = self.get_equilateral_triangle_points(self.start_pos, end_pos)
                if points:
                    self.shapes.append(
                        {
                            "type": "equilateral_triangle",
                            "points": points,
                            "color": self.current_color,
                            "width": self.shape_border_width,
                        }
                    )
                    self.rebuild_canvas()

            elif self.current_tool == "rhombus":
                points = self.get_rhombus_points(self.start_pos, end_pos)
                if points:
                    self.shapes.append(
                        {
                            "type": "rhombus",
                            "points": points,
                            "color": self.current_color,
                            "width": self.shape_border_width,
                        }
                    )
                    self.rebuild_canvas()

        self.is_drawing = False
        self.start_pos = None
        self.current_pos = None
        self.active_stroke_points = []

    def draw_toolbar(self) -> None:
        pygame.draw.rect(self.screen, (230, 230, 235), (0, 0, WINDOW_WIDTH, TOOLBAR_HEIGHT))
        pygame.draw.line(self.screen, (170, 170, 180), (0, TOOLBAR_HEIGHT), (WINDOW_WIDTH, TOOLBAR_HEIGHT), 2)

        name_map = {
            "pen": "PEN",
            "rectangle": "RECT",
            "circle": "CIRCLE",
            "square": "SQUARE",
            "right_triangle": "R-TRI",
            "equilateral_triangle": "EQ-TRI",
            "rhombus": "RHOMBUS",
            "eraser": "ERASER",
        }

        for tool_name, rect in self.tools:
            fill = (85, 145, 255) if tool_name == self.current_tool else (205, 210, 220)
            pygame.draw.rect(self.screen, fill, rect, border_radius=8)
            pygame.draw.rect(self.screen, (100, 100, 110), rect, width=2, border_radius=8)

            label = self.font.render(name_map[tool_name], True, (20, 20, 25))
            self.screen.blit(label, label.get_rect(center=rect.center))

        for color, rect in self.colors:
            pygame.draw.rect(self.screen, color, rect, border_radius=5)
            border_color = (0, 0, 0) if color == self.current_color else (95, 95, 105)
            border_width = 3 if color == self.current_color else 1
            pygame.draw.rect(self.screen, border_color, rect, width=border_width, border_radius=5)

        info_text = self.font.render(
            "Left drag = draw | Eraser left drag = manual erase | Right click = delete shape",
            True,
            (32, 32, 42),
        )
        self.screen.blit(info_text, (12, 86))

    def draw_preview_shape(self) -> None:
        if not self.is_drawing:
            return
        if self.start_pos is None or self.current_pos is None:
            return

        if self.current_tool == "pen":
            shifted = [(x, y + TOOLBAR_HEIGHT) for x, y in self.active_stroke_points]
            if len(shifted) == 1:
                pygame.draw.circle(self.screen, self.current_color, shifted[0], max(1, self.pen_size // 2))
            elif len(shifted) > 1:
                pygame.draw.lines(self.screen, self.current_color, False, shifted, self.pen_size)
            return

        if self.current_tool == "eraser":
            shifted = [(x, y + TOOLBAR_HEIGHT) for x, y in self.active_stroke_points]
            if len(shifted) == 1:
                pygame.draw.circle(self.screen, (255, 255, 255), shifted[0], max(1, self.eraser_size // 2))
            elif len(shifted) > 1:
                pygame.draw.lines(self.screen, (255, 255, 255), False, shifted, self.eraser_size)
            return

        if self.current_tool == "rectangle":
            rect = self.get_drag_rect(self.start_pos, self.current_pos).move(0, TOOLBAR_HEIGHT)
            pygame.draw.rect(self.screen, self.current_color, rect, width=2)
            return

        if self.current_tool == "circle":
            rect = self.get_drag_rect(self.start_pos, self.current_pos).move(0, TOOLBAR_HEIGHT)
            pygame.draw.ellipse(self.screen, self.current_color, rect, width=2)
            return

        if self.current_tool == "square":
            square_rect = self.get_square_rect(self.start_pos, self.current_pos)
            if square_rect is not None:
                pygame.draw.rect(self.screen, self.current_color, square_rect.move(0, TOOLBAR_HEIGHT), width=2)
            return

        if self.current_tool == "right_triangle":
            points = self.get_right_triangle_points(self.start_pos, self.current_pos)
            if points:
                shifted = [(x, y + TOOLBAR_HEIGHT) for x, y in points]
                pygame.draw.polygon(self.screen, self.current_color, shifted, width=2)
            return

        if self.current_tool == "equilateral_triangle":
            points = self.get_equilateral_triangle_points(self.start_pos, self.current_pos)
            if points:
                shifted = [(x, y + TOOLBAR_HEIGHT) for x, y in points]
                pygame.draw.polygon(self.screen, self.current_color, shifted, width=2)
            return

        if self.current_tool == "rhombus":
            points = self.get_rhombus_points(self.start_pos, self.current_pos)
            if points:
                shifted = [(x, y + TOOLBAR_HEIGHT) for x, y in points]
                pygame.draw.polygon(self.screen, self.current_color, shifted, width=2)

    def draw_delete_highlight(self) -> None:
        mouse_pos = pygame.mouse.get_pos()
        canvas_pos = self.get_canvas_pos(mouse_pos)
        if canvas_pos is None:
            return

        index = self.get_shape_index_at_point(canvas_pos)
        if index == -1:
            return

        shape = self.shapes[index]
        shape_type = str(shape["type"])

        if shape_type in {"rectangle", "circle", "square"}:
            rect = pygame.Rect(shape["rect"])  # type: ignore[arg-type]
            highlight_rect = rect.inflate(10, 10).move(0, TOOLBAR_HEIGHT)
        elif shape_type in {"right_triangle", "equilateral_triangle", "rhombus"}:
            points = list(shape["points"])  # type: ignore[arg-type]
            highlight_rect = self.points_bounding_rect(points).inflate(16, 16).move(0, TOOLBAR_HEIGHT)
        else:
            points = list(shape["points"])  # type: ignore[arg-type]
            highlight_rect = self.points_bounding_rect(points).inflate(16, 16).move(0, TOOLBAR_HEIGHT)

        pygame.draw.rect(self.screen, (255, 80, 80), highlight_rect, width=2, border_radius=5)

    def draw_custom_cursor(self) -> None:
        mouse_x, mouse_y = pygame.mouse.get_pos()

        if self.current_tool == "pen":
            self.screen.blit(self.pen_cursor, (mouse_x - self.pen_hotspot[0], mouse_y - self.pen_hotspot[1]))
            return

        if self.current_tool == "eraser":
            self.screen.blit(
                self.eraser_cursor,
                (mouse_x - self.eraser_hotspot[0], mouse_y - self.eraser_hotspot[1]),
            )
            return

        pygame.draw.line(self.screen, (35, 35, 35), (mouse_x - 8, mouse_y), (mouse_x + 8, mouse_y), 1)
        pygame.draw.line(self.screen, (35, 35, 35), (mouse_x, mouse_y - 8), (mouse_x, mouse_y + 8), 1)

    def draw(self) -> None:
        self.screen.fill((240, 240, 244))
        self.screen.blit(self.canvas, (0, TOOLBAR_HEIGHT))
        self.draw_toolbar()
        self.draw_preview_shape()
        self.draw_delete_highlight()
        self.draw_custom_cursor()

    def run(self) -> None:
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.handle_left_mouse_down(event.pos)

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                    self.handle_right_mouse_down(event.pos)

                elif event.type == pygame.MOUSEMOTION:
                    self.handle_mouse_motion(event.pos)

                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.handle_left_mouse_up(event.pos)

            self.draw()
            pygame.display.flip()
            self.clock.tick(60)

        pygame.mouse.set_visible(True)
        pygame.quit()


def run_paint_app() -> None:
    app = PaintApp()
    app.run()