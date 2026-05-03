import pygame
import math
import sys
from datetime import datetime
from pathlib import Path

# Import our helper tools from tools.py
sys.path.insert(0, str(Path(__file__).resolve().parent))
from tools import BRUSH_SIZES, flood_fill

WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
TOOLBAR_HEIGHT = 140          # space at the top for buttons and palette
CANVAS_WIDTH = WINDOW_WIDTH
CANVAS_HEIGHT = WINDOW_HEIGHT - TOOLBAR_HEIGHT  # drawable area below toolbar

TOOL_NAMES = [
    "pencil",    "line",      "rectangle", "circle",
    "square",    "right_tri", "eq_tri",    "rhombus",
    "eraser",    "fill",      "text",
]

# Human-readable labels for the buttons
TOOL_LABELS = {
    "pencil":    "PENCIL",
    "line":      "LINE",
    "rectangle": "RECT",
    "circle":    "CIRCLE",
    "square":    "SQUARE",
    "right_tri": "R-TRI",
    "eq_tri":    "EQ-TRI",
    "rhombus":   "RHOMBUS",
    "eraser":    "ERASER",
    "fill":      "FILL",
    "text":      "TEXT",
}

# Color palette — 10 colors in 2 rows of 5
PALETTE = [
    (0,   0,   0  ),   # black
    (210, 0,   0  ),   # red
    (0,   110, 230),   # blue
    (0,   170, 60 ),   # green
    (255, 165, 0  ),   # orange
    (155, 30,  220),   # purple
    (0,   200, 200),   # cyan
    (180, 50,  50 ),   # dark red
    (130, 130, 130),   # gray
    (255, 255, 255),   # white
]

# Labels for the size buttons (keyboard shortcuts shown in brackets)
SIZE_LABELS = ["S (1)", "M (2)", "L (3)"]

class PaintApp:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("TSIS 02 - Paint Extended")

        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()

        # Font for toolbar button labels
        self.font = pygame.font.SysFont("arial", 14, bold=True)
        # Larger font for text tool input
        self.text_font = pygame.font.SysFont("arial", 22)
        # Small font for the hint bar at the bottom of the toolbar
        self.hint_font = pygame.font.SysFont("arial", 13)

        # Canvas is the white drawing area — all shapes are rendered here
        self.canvas = pygame.Surface((CANVAS_WIDTH, CANVAS_HEIGHT))
        self.canvas.fill((255, 255, 255))

        # Toolbar button lists — filled in by build_toolbar()
        self.tool_buttons = []   # list of (name, pygame.Rect)
        self.color_buttons = []  # list of (color_tuple, pygame.Rect)
        self.size_buttons = []   # list of (size_index, pygame.Rect)
        self.build_toolbar()

        # Currently active tool, color, and brush size index
        self.current_tool = "pencil"
        self.current_color = (0, 0, 0)
        self.brush_size_idx = 1  # 0=small, 1=medium, 2=large

        # Stored shapes — each shape is a dictionary describing what to draw.
        # rebuild_canvas() redraws all of them from scratch.
        self.shapes = []
        self.erase_strokes = []

        # Flood fills and text are stored separately so they survive
        # a rebuild triggered by right-click shape deletion.
        self.fills = []   # list of {"pos": (x,y), "color": (r,g,b)}
        self.texts = []   # list of {"pos": (x,y), "text": str, "color": (r,g,b)}

        # State for drawing in progress
        self.is_drawing = False
        self.start_pos = None    # where the mouse was pressed
        self.current_pos = None  # where the mouse is now
        self.active_stroke = []  # collected points for pencil/eraser

        # State for the text tool
        self.text_active = False   # are we typing right now?
        self.text_pos = None       # where on canvas the text starts
        self.text_buffer = ""      # characters typed so far

        # Save notification — shows filename briefly after Ctrl+S
        self.save_message = None   # (message_string, timestamp_ms)

        # Custom cursors
        self.pen_cursor, self.pen_hotspot = self.make_pen_cursor()
        self.eraser_cursor, self.eraser_hotspot = self.make_eraser_cursor()
        pygame.mouse.set_visible(False)  # hide the default OS cursor

    def brush_size(self):
        return BRUSH_SIZES[self.brush_size_idx]

    def build_toolbar(self):
        # Tool buttons: 3 rows x 4 columns 
        btn_w, btn_h = 112, 28
        btn_x0, btn_y0 = 8, 8
        gap_x, gap_y = 5, 5

        for i, name in enumerate(TOOL_NAMES):
            row = i // 4
            col = i % 4
            x = btn_x0 + col * (btn_w + gap_x)
            y = btn_y0 + row * (btn_h + gap_y)
            self.tool_buttons.append((name, pygame.Rect(x, y, btn_w, btn_h)))

        # Color swatches: 2 rows x 5 columns 
        swatch_size = 26
        swatch_gap = 4
        swatch_x0 = 500
        swatch_y0 = 8

        for i, color in enumerate(PALETTE):
            row = i // 5
            col = i % 5
            x = swatch_x0 + col * (swatch_size + swatch_gap)
            y = swatch_y0 + row * (swatch_size + swatch_gap)
            self.color_buttons.append((color, pygame.Rect(x, y, swatch_size, swatch_size)))

        # Size buttons: S, M, L stacked vertically 
        size_x = 672
        size_w, size_h, size_gap = 62, 28, 5

        for i in range(3):
            y = btn_y0 + i * (size_h + size_gap)
            self.size_buttons.append((i, pygame.Rect(size_x, y, size_w, size_h)))

    def get_canvas_pos(self, screen_pos):
        sx, sy = screen_pos
        cy = sy - TOOLBAR_HEIGHT
        if 0 <= sx < CANVAS_WIDTH and 0 <= cy < CANVAS_HEIGHT:
            return (sx, cy)
        return None

    def make_pen_cursor(self):
        surf = pygame.Surface((26, 26), pygame.SRCALPHA)
        pygame.draw.polygon(surf, (60, 70, 85),    [(5, 3), (21, 19), (16, 24), (0, 8)])
        pygame.draw.polygon(surf, (120, 136, 154), [(7, 4), (17, 14), (14, 17), (4, 7)])
        pygame.draw.polygon(surf, (236, 216, 175), [(16, 24), (22, 18), (24, 20), (18, 26)])
        pygame.draw.polygon(surf, (40, 40, 40),    [(20, 22), (24, 20), (22, 24)])
        return surf, (20, 22)

    def make_eraser_cursor(self):
        surf = pygame.Surface((26, 26), pygame.SRCALPHA)
        pygame.draw.rect(surf, (245, 127, 151), (4, 6, 18, 14), border_radius=4)
        pygame.draw.rect(surf, (255, 255, 255), (4, 6,  9, 14), border_radius=4)
        pygame.draw.rect(surf, (95, 95, 100),   (4, 6, 18, 14), width=2, border_radius=4)
        return surf, (13, 13)


    def drag_rect(self, a, b):
        # Bounding rectangle that covers the drag from a to b
        return pygame.Rect(
            min(a[0], b[0]), min(a[1], b[1]),
            abs(a[0] - b[0]), abs(a[1] - b[1])
        )

    def square_rect(self, a, b):
        # Like drag_rect but forces equal width and height
        dx = b[0] - a[0]
        dy = b[1] - a[1]
        side = min(abs(dx), abs(dy))
        if side == 0:
            return None
        x = a[0] if dx >= 0 else a[0] - side
        y = a[1] if dy >= 0 else a[1] - side
        return pygame.Rect(x, y, side, side)

    def right_tri_points(self, a, b):
        r = self.drag_rect(a, b)
        if r.width == 0 or r.height == 0:
            return []
        return [(r.left, r.bottom), (r.left, r.top), (r.right, r.bottom)]

    def eq_tri_points(self, a, b):
        r = self.drag_rect(a, b)
        if r.width == 0 or r.height == 0:
            return []
        side = r.width
        tri_h = int(math.sqrt(3) / 2 * side)
        # Shrink if the triangle is too tall for the bounding box
        if tri_h > r.height:
            side = max(2, int(r.height / (math.sqrt(3) / 2)))
            tri_h = int(math.sqrt(3) / 2 * side)
        cx = r.centerx
        top_y = r.top + (r.height - tri_h) // 2
        return [
            (cx, top_y),
            (cx - side // 2, top_y + tri_h),
            (cx + side // 2, top_y + tri_h),
        ]

    def rhombus_points(self, a, b):
        r = self.drag_rect(a, b)
        if r.width == 0 or r.height == 0:
            return []
        return [
            (r.centerx, r.top),
            (r.right,   r.centery),
            (r.centerx, r.bottom),
            (r.left,    r.centery),
        ]

    def points_bbox(self, pts):
        # Smallest rectangle that contains all the given points
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        return pygame.Rect(min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))

    def seg_dist(self, point, a, b):
        # Distance from a point to a line segment (a → b)
        px, py = point
        ax, ay = a
        bx, by = b
        dx, dy = bx - ax, by - ay
        if dx == 0 and dy == 0:
            return math.hypot(px - ax, py - ay)
        t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
        return math.hypot(px - ax - t * dx, py - ay - t * dy)

    def draw_shape(self, surface, shape):
        shape_type = shape["type"]
        color = tuple(shape["color"])
        width = int(shape["width"])

        if shape_type == "stroke":
            # Freehand pencil or eraser stroke
            pts = list(shape["points"])
            if len(pts) == 1:
                pygame.draw.circle(surface, color, pts[0], max(1, width // 2))
            else:
                pygame.draw.lines(surface, color, False, pts, width)

        elif shape_type == "line":
            # Straight line from p1 to p2
            pygame.draw.line(surface, color, tuple(shape["p1"]), tuple(shape["p2"]), width)

        elif shape_type in ("rectangle", "square"):
            pygame.draw.rect(surface, color, pygame.Rect(shape["rect"]), width=width)

        elif shape_type == "circle":
            pygame.draw.ellipse(surface, color, pygame.Rect(shape["rect"]), width=width)

        elif shape_type in ("right_tri", "eq_tri", "rhombus"):
            pygame.draw.polygon(surface, color, list(shape["points"]), width=width)

    def rebuild_canvas(self):
        self.canvas.fill((255, 255, 255))

        # Redraw all vector shapes
        for shape in self.shapes:
            self.draw_shape(self.canvas, shape)

        # Apply eraser strokes (white lines on top)
        for stroke in self.erase_strokes:
            self.draw_shape(self.canvas, stroke)

        # Replay every flood fill in the order they were made
        for f in self.fills:
            flood_fill(self.canvas, f["pos"], f["color"])

        # Replay every text label
        for t in self.texts:
            rendered = self.text_font.render(t["text"], True, t["color"])
            self.canvas.blit(rendered, t["pos"])

    def shape_hit(self, pt, shape):
        shape_type = shape["type"]

        if shape_type == "stroke":
            pts = list(shape["points"])
            thresh = max(6, int(shape["width"]) + 3)
            if len(pts) == 1:
                return math.hypot(pt[0] - pts[0][0], pt[1] - pts[0][1]) <= thresh
            for i in range(len(pts) - 1):
                if self.seg_dist(pt, pts[i], pts[i + 1]) <= thresh:
                    return True
            return False

        if shape_type == "line":
            thresh = max(6, int(shape["width"]) + 3)
            return self.seg_dist(pt, tuple(shape["p1"]), tuple(shape["p2"])) <= thresh

        if shape_type in ("rectangle", "circle", "square"):
            return pygame.Rect(shape["rect"]).inflate(8, 8).collidepoint(pt)

        if shape_type in ("right_tri", "eq_tri", "rhombus"):
            return self.points_bbox(list(shape["points"])).inflate(8, 8).collidepoint(pt)

        return False

    def save_canvas(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_dir = Path(__file__).resolve().parent
        filename = str(save_dir / f"screens\canvas_{timestamp}.png")
        pygame.image.save(self.canvas, filename)
        # Show a brief confirmation message in the toolbar
        self.save_message = (f"Saved: canvas_{timestamp}.png", pygame.time.get_ticks())

    def commit_text(self):
        if not self.text_buffer or self.text_pos is None:
            return
        # Store so it survives a rebuild
        self.texts.append({
            "pos": self.text_pos,
            "text": self.text_buffer,
            "color": self.current_color,
        })
        # Draw immediately to canvas
        rendered = self.text_font.render(self.text_buffer, True, self.current_color)
        self.canvas.blit(rendered, self.text_pos)

    def handle_keydown(self, event):
        # Text mode: route all keys to text input 
        if self.text_active:
            if event.key == pygame.K_RETURN:
                # Confirm and burn text onto canvas
                self.commit_text()
                self.text_active = False
                self.text_buffer = ""
                self.text_pos = None
            elif event.key == pygame.K_ESCAPE:
                # Cancel text input without drawing anything
                self.text_active = False
                self.text_buffer = ""
                self.text_pos = None
            elif event.key == pygame.K_BACKSPACE:
                self.text_buffer = self.text_buffer[:-1]
            elif event.unicode and event.unicode.isprintable():
                self.text_buffer += event.unicode
            return  # don't process global shortcuts while typing

        mods = pygame.key.get_mods()

        if event.key == pygame.K_ESCAPE:
            # Post a QUIT event to cleanly exit the main loop
            pygame.event.post(pygame.event.Event(pygame.QUIT))

        elif event.key == pygame.K_s and (mods & pygame.KMOD_CTRL):
            # Ctrl+S → save canvas as PNG
            self.save_canvas()

        elif event.key == pygame.K_1: # Keydown 1 / 2 / 3
            self.brush_size_idx = 0   # small
        elif event.key == pygame.K_2:
            self.brush_size_idx = 1   # medium
        elif event.key == pygame.K_3:
            self.brush_size_idx = 2   # large

    def handle_left_down(self, pos):
        # Check if a tool button was clicked
        for name, rect in self.tool_buttons:
            if rect.collidepoint(pos):
                self.current_tool = name
                self.text_active = False  # cancel text if tool changes
                return

        # Check if a color swatch was clicked
        for color, rect in self.color_buttons:
            if rect.collidepoint(pos):
                self.current_color = color
                return

        # Check if a size button was clicked
        for idx, rect in self.size_buttons:
            if rect.collidepoint(pos):
                self.brush_size_idx = idx
                return

        # Everything below only applies to the canvas area
        canvas_pos = self.get_canvas_pos(pos)
        if canvas_pos is None:
            return

        # Fill tool: flood fill on click 
        if self.current_tool == "fill":
            # Store the fill so it survives rebuild_canvas()
            self.fills.append({"pos": canvas_pos, "color": self.current_color})
            # Apply immediately to canvas
            flood_fill(self.canvas, canvas_pos, self.current_color)
            return

        # Text tool: place the text cursor 
        if self.current_tool == "text":
            self.text_active = True
            self.text_pos = canvas_pos
            self.text_buffer = ""
            return

        # All drawing tools: start a drag 
        self.is_drawing = True
        self.start_pos = canvas_pos
        self.current_pos = canvas_pos # start collecting points

        if self.current_tool in ("pencil", "eraser"):
            self.active_stroke = [canvas_pos]

    def handle_motion(self, pos):
        if not self.is_drawing:
            return
        canvas_pos = self.get_canvas_pos(pos)
        if canvas_pos is None:
            return
        self.current_pos = canvas_pos
        # For freehand tools, collect each new point along the path
        if self.current_tool in ("pencil", "eraser"):
            if not self.active_stroke or self.active_stroke[-1] != canvas_pos:
                self.active_stroke.append(canvas_pos) # adding each point of the path

    def handle_right_down(self, pos): # Delete Shape
        canvas_pos = self.get_canvas_pos(pos)
        if canvas_pos is None:
            return
        # Search from newest to oldest shape
        for i in range(len(self.shapes) - 1, -1, -1):
            if self.shape_hit(canvas_pos, self.shapes[i]):
                del self.shapes[i]
                self.rebuild_canvas()
                return

    def handle_left_up(self, pos): # completes the drawing of the shape
        if not self.is_drawing:
            return
        end = self.get_canvas_pos(pos)
        if end is None:
            end = self.current_pos  # clamp to last known canvas position
        if self.start_pos and end:
            self.commit_shape(end)
        self.is_drawing = False
        self.start_pos = None
        self.current_pos = None
        self.active_stroke = []

    def commit_shape(self, end):
        tool = self.current_tool
        bs = self.brush_size()
        sp = self.start_pos

        if tool == "pencil" and self.active_stroke:
            self.shapes.append({
                "type": "stroke",
                "points": list(self.active_stroke),
                "color": self.current_color,
                "width": bs,
            })
            self.rebuild_canvas()

        elif tool == "line":
            self.shapes.append({
                "type": "line",
                "p1": sp,
                "p2": end,
                "color": self.current_color,
                "width": bs,
            })
            self.rebuild_canvas()

        elif tool == "eraser" and self.active_stroke:
            # Eraser is just a white stroke — stored separately from shapes
            self.erase_strokes.append({
                "type": "stroke",
                "points": list(self.active_stroke),
                "color": (255, 255, 255),
                "width": 22,  # fixed eraser thickness
            })
            self.rebuild_canvas()

        elif tool == "rectangle":
            r = self.drag_rect(sp, end)
            if r.width > 0 and r.height > 0:
                self.shapes.append({
                    "type": "rectangle",
                    "rect": r,
                    "color": self.current_color,
                    "width": bs,
                })
                self.rebuild_canvas()

        elif tool == "circle":
            r = self.drag_rect(sp, end)
            if r.width > 0 and r.height > 0:
                self.shapes.append({
                    "type": "circle",
                    "rect": r,
                    "color": self.current_color,
                    "width": bs,
                })
                self.rebuild_canvas()

        elif tool == "square":
            r = self.square_rect(sp, end)
            if r:
                self.shapes.append({
                    "type": "square",
                    "rect": r,
                    "color": self.current_color,
                    "width": bs,
                })
                self.rebuild_canvas()

        elif tool == "right_tri":
            pts = self.right_tri_points(sp, end)
            if pts:
                self.shapes.append({
                    "type": "right_tri",
                    "points": pts,
                    "color": self.current_color,
                    "width": bs,
                })
                self.rebuild_canvas()

        elif tool == "eq_tri":
            pts = self.eq_tri_points(sp, end)
            if pts:
                self.shapes.append({
                    "type": "eq_tri",
                    "points": pts,
                    "color": self.current_color,
                    "width": bs,
                })
                self.rebuild_canvas()

        elif tool == "rhombus":
            pts = self.rhombus_points(sp, end)
            if pts:
                self.shapes.append({
                    "type": "rhombus",
                    "points": pts,
                    "color": self.current_color,
                    "width": bs,
                })
                self.rebuild_canvas()

    def draw_toolbar(self):
        # Toolbar background
        pygame.draw.rect(self.screen, (228, 230, 238), (0, 0, WINDOW_WIDTH, TOOLBAR_HEIGHT))
        # Dividing line between toolbar and canvas
        pygame.draw.line(self.screen, (155, 158, 175),
                         (0, TOOLBAR_HEIGHT), (WINDOW_WIDTH, TOOLBAR_HEIGHT), 2)

        # Draw each tool button
        for name, rect in self.tool_buttons:
            is_active = (name == self.current_tool)
            fill_color = (75, 140, 255) if is_active else (205, 210, 222)
            pygame.draw.rect(self.screen, fill_color, rect, border_radius=7)
            pygame.draw.rect(self.screen, (90, 90, 105), rect, width=1, border_radius=7)
            label_color = (255, 255, 255) if is_active else (20, 20, 30)
            label = self.font.render(TOOL_LABELS[name], True, label_color)
            self.screen.blit(label, label.get_rect(center=rect.center))

        # Draw each color swatch
        for color, rect in self.color_buttons:
            pygame.draw.rect(self.screen, color, rect, border_radius=4)
            # Highlight the currently selected color with a thicker border
            if color == self.current_color:
                pygame.draw.rect(self.screen, (10, 10, 10), rect, width=3, border_radius=4)
            else:
                pygame.draw.rect(self.screen, (90, 90, 100), rect, width=1, border_radius=4)

        # Draw each size button
        for idx, rect in self.size_buttons:
            is_active = (idx == self.brush_size_idx)
            fill_color = (75, 140, 255) if is_active else (205, 210, 222)
            pygame.draw.rect(self.screen, fill_color, rect, border_radius=6)
            pygame.draw.rect(self.screen, (90, 90, 105), rect, width=1, border_radius=6)
            label_color = (255, 255, 255) if is_active else (20, 20, 30)
            label = self.font.render(SIZE_LABELS[idx], True, label_color)
            self.screen.blit(label, label.get_rect(center=rect.center))

        # Hint bar at the bottom of the toolbar
        if self.text_active:
            hint = f'TEXT MODE  typing: "{self.text_buffer}"  |  Enter = confirm   Esc = cancel'
        else:
            hint = ("Drag = draw   |   Right-click = delete shape   |   "
                    "1/2/3 = brush size   |   Ctrl+S = save PNG   |   Esc = quit")
        hint_surf = self.hint_font.render(hint, True, (50, 50, 60))
        self.screen.blit(hint_surf, (8, 118))

        # Save confirmation message — shown for 3 seconds
        if self.save_message:
            msg, ts = self.save_message
            if pygame.time.get_ticks() - ts < 3000:
                saved_surf = self.hint_font.render(msg, True, (20, 130, 20))
                self.screen.blit(saved_surf, (750, 118))
            else:
                self.save_message = None

    def draw_preview(self):
        # Show a live preview of text while the user types
        if self.text_active and self.text_pos is not None:
            preview = self.text_font.render(self.text_buffer + "|", True, self.current_color)
            # Shift y by TOOLBAR_HEIGHT because text_pos is canvas-relative
            screen_x = self.text_pos[0]
            screen_y = self.text_pos[1] + TOOLBAR_HEIGHT
            self.screen.blit(preview, (screen_x, screen_y))
            return

        if not self.is_drawing or self.start_pos is None or self.current_pos is None:
            return

        sp = self.start_pos
        cp = self.current_pos
        col = self.current_color
        bs = self.brush_size()
        tool = self.current_tool

        # Pencil preview — draw the stroke on screen as the mouse moves
        if tool == "pencil":
            shifted = [(x, y + TOOLBAR_HEIGHT) for x, y in self.active_stroke]
            if len(shifted) == 1:
                pygame.draw.circle(self.screen, col, shifted[0], max(1, bs // 2))
            elif len(shifted) > 1:
                pygame.draw.lines(self.screen, col, False, shifted, bs)

        # Eraser preview — white stroke on screen
        elif tool == "eraser":
            shifted = [(x, y + TOOLBAR_HEIGHT) for x, y in self.active_stroke]
            if len(shifted) == 1:
                pygame.draw.circle(self.screen, (255, 255, 255), shifted[0], 11)
            elif len(shifted) > 1:
                pygame.draw.lines(self.screen, (255, 255, 255), False, shifted, 22)

        # Straight line preview
        elif tool == "line":
            p1 = (sp[0], sp[1] + TOOLBAR_HEIGHT)
            p2 = (cp[0], cp[1] + TOOLBAR_HEIGHT)
            pygame.draw.line(self.screen, col, p1, p2, max(1, bs))

        # Rectangle preview
        elif tool == "rectangle":
            r = self.drag_rect(sp, cp).move(0, TOOLBAR_HEIGHT)
            pygame.draw.rect(self.screen, col, r, width=max(1, bs))

        # Circle (ellipse) preview
        elif tool == "circle":
            r = self.drag_rect(sp, cp).move(0, TOOLBAR_HEIGHT)
            pygame.draw.ellipse(self.screen, col, r, width=max(1, bs))

        # Square preview
        elif tool == "square":
            r = self.square_rect(sp, cp)
            if r:
                pygame.draw.rect(self.screen, col, r.move(0, TOOLBAR_HEIGHT), width=max(1, bs))

        # Right-triangle preview
        elif tool == "right_tri":
            pts = self.right_tri_points(sp, cp)
            if pts:
                shifted = [(x, y + TOOLBAR_HEIGHT) for x, y in pts]
                pygame.draw.polygon(self.screen, col, shifted, width=max(1, bs))

        # Equilateral-triangle preview
        elif tool == "eq_tri":
            pts = self.eq_tri_points(sp, cp)
            if pts:
                shifted = [(x, y + TOOLBAR_HEIGHT) for x, y in pts]
                pygame.draw.polygon(self.screen, col, shifted, width=max(1, bs))

        # Rhombus preview
        elif tool == "rhombus":
            pts = self.rhombus_points(sp, cp)
            if pts:
                shifted = [(x, y + TOOLBAR_HEIGHT) for x, y in pts]
                pygame.draw.polygon(self.screen, col, shifted, width=max(1, bs))

    def draw_cursor(self):
        mx, my = pygame.mouse.get_pos()

        if self.current_tool == "pencil":
            self.screen.blit(self.pen_cursor,
                             (mx - self.pen_hotspot[0], my - self.pen_hotspot[1]))

        elif self.current_tool == "eraser":
            self.screen.blit(self.eraser_cursor,
                             (mx - self.eraser_hotspot[0], my - self.eraser_hotspot[1]))

        elif self.current_tool == "text":
            # I-beam cursor
            pygame.draw.line(self.screen, (30, 30, 30), (mx, my - 10), (mx, my + 10), 2)
            pygame.draw.line(self.screen, (30, 30, 30), (mx - 4, my - 10), (mx + 4, my - 10), 2)
            pygame.draw.line(self.screen, (30, 30, 30), (mx - 4, my + 10), (mx + 4, my + 10), 2)

        elif self.current_tool == "fill":
            # Crosshair with a small filled dot showing the current color
            pygame.draw.line(self.screen, (30, 30, 30), (mx - 8, my), (mx + 8, my), 1)
            pygame.draw.line(self.screen, (30, 30, 30), (mx, my - 8), (mx, my + 8), 1)
            pygame.draw.circle(self.screen, self.current_color, (mx + 5, my + 5), 4)

        else:
            # Simple crosshair for shape tools and line tool
            pygame.draw.line(self.screen, (30, 30, 30), (mx - 8, my), (mx + 8, my), 1)
            pygame.draw.line(self.screen, (30, 30, 30), (mx, my - 8), (mx, my + 8), 1)

    def draw(self):
        # Background behind the canvas
        self.screen.fill((220, 222, 228))
        # Canvas goes below the toolbar
        self.screen.blit(self.canvas, (0, TOOLBAR_HEIGHT))
        self.draw_toolbar()
        self.draw_preview()
        self.draw_cursor()

    def run(self):
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    self.handle_keydown(event)

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.handle_left_down(event.pos) # 

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                    self.handle_right_down(event.pos)

                elif event.type == pygame.MOUSEMOTION:
                    self.handle_motion(event.pos)

                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.handle_left_up(event.pos)

            self.draw()
            pygame.display.flip()
            self.clock.tick(60)

        pygame.mouse.set_visible(True)
        pygame.quit()


# Entry point
if __name__ == "__main__":
    app = PaintApp()
    app.run()