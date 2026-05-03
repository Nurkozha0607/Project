# game.py — Core game logic (Snake, Food, PowerUps, Obstacles, Renderer)

import pygame
import random
import math
from config import *


# ─────────────────────────── helpers ────────────────────────────────────────

def random_cell(exclude: set = None) -> tuple:
    """Return a random (col, row) not in *exclude*."""
    exclude = exclude or set()
    while True:
        cell = (random.randint(0, COLS - 1), random.randint(0, ROWS - 1))
        if cell not in exclude:
            return cell


# ─────────────────────────── Snake ──────────────────────────────────────────

class Snake:
    def __init__(self, color=GREEN):
        cx, cy = COLS // 2, ROWS // 2
        self.body      = [(cx, cy), (cx - 1, cy), (cx - 2, cy)]
        self.direction = (1, 0)
        self.pending   = (1, 0)
        self.color     = color
        self.grow_pending = 0

    # ── input ──
    def set_direction(self, dx, dy):
        # Prevent 180-degree reversal
        if (dx, dy) != (-self.direction[0], -self.direction[1]):
            self.pending = (dx, dy)

    # ── update ──
    def move(self):
        self.direction = self.pending
        head = (self.body[0][0] + self.direction[0],
                self.body[0][1] + self.direction[1])
        self.body.insert(0, head)
        if self.grow_pending > 0:
            self.grow_pending -= 1
        else:
            self.body.pop()

    def grow(self, n=1):
        self.grow_pending += n

    def shorten(self, n=2) -> bool:
        """Remove *n* tail segments. Returns False if length would drop ≤ 1."""
        if len(self.body) - n <= 1:
            return False
        self.body = self.body[:max(1, len(self.body) - n)]
        return True

    # ── queries ──
    @property
    def head(self):
        return self.body[0]

    def occupies(self) -> set:
        return set(self.body)

    def self_collision(self) -> bool:
        return self.body[0] in self.body[1:]

    def wall_collision(self) -> bool:
        x, y = self.body[0]
        return x < 0 or x >= COLS or y < 0 or y >= ROWS

    # ── draw ──
    def draw(self, surface, cell_size=CELL_SIZE, hud_h=HUD_HEIGHT):
        for i, (cx, cy) in enumerate(self.body):
            rect = pygame.Rect(cx * cell_size, hud_h + cy * cell_size,
                               cell_size, cell_size)
            shade = max(40, self.color[1] - i * 4)
            seg_color = (self.color[0],
                         min(255, max(0, self.color[1] - i * 3)),
                         self.color[2])
            pygame.draw.rect(surface, seg_color, rect, border_radius=4)
            if i == 0:  # head highlight
                pygame.draw.rect(surface, WHITE,
                                 rect.inflate(-8, -8), border_radius=2)


# ─────────────────────────── Food ───────────────────────────────────────────

class FoodItem:
    NORMAL = "normal"
    RARE   = "rare"
    POISON = "poison"

    def __init__(self, pos, kind):
        self.pos        = pos
        self.kind       = kind
        self.spawn_time = pygame.time.get_ticks()

    @property
    def color(self):
        return {self.NORMAL: FOOD_NORMAL_COLOR,
                self.RARE:   FOOD_RARE_COLOR,
                self.POISON: FOOD_POISON_COLOR}[self.kind]

    @property
    def points(self):
        return {self.NORMAL: POINTS_NORMAL,
                self.RARE:   POINTS_RARE,
                self.POISON: 0}[self.kind]

    def is_expired(self) -> bool:
        return (pygame.time.get_ticks() - self.spawn_time) > FOOD_DISAPPEAR_SEC * 1000

    def draw(self, surface, cell_size=CELL_SIZE, hud_h=HUD_HEIGHT):
        cx, cy = self.pos
        rect   = pygame.Rect(cx * cell_size, hud_h + cy * cell_size,
                             cell_size, cell_size)
        # Pulsing alpha circle
        t      = pygame.time.get_ticks() / 400
        r      = int(cell_size // 2 - 1 + 2 * abs(math.sin(t)))
        center = rect.center
        pygame.draw.circle(surface, self.color, center, r)
        if self.kind == self.RARE:
            pygame.draw.circle(surface, WHITE, center, r - 3, 1)
        if self.kind == self.POISON:
            pygame.draw.circle(surface, (200, 0, 0), center, r - 3, 1)


class FoodManager:
    MAX_FOOD   = 3
    MAX_POISON = 1

    def __init__(self):
        self.items: list[FoodItem] = []

    def blocked(self) -> set:
        return {f.pos for f in self.items}

    def spawn(self, blocked: set):
        """Spawn food until we reach MAX_FOOD and MAX_POISON limits."""
        all_blocked = blocked | self.blocked()
        normal_count = sum(1 for f in self.items if f.kind != FoodItem.POISON)
        poison_count = sum(1 for f in self.items if f.kind == FoodItem.POISON)

        while normal_count < self.MAX_FOOD:
            pos  = random_cell(all_blocked)
            kind = (FoodItem.RARE
                    if random.random() < FOOD_RARE_WEIGHT / (FOOD_NORMAL_WEIGHT + FOOD_RARE_WEIGHT)
                    else FoodItem.NORMAL)
            self.items.append(FoodItem(pos, kind))
            all_blocked.add(pos)
            normal_count += 1

        if poison_count < self.MAX_POISON and random.random() < POISON_CHANCE:
            pos = random_cell(all_blocked)
            self.items.append(FoodItem(pos, FoodItem.POISON))

    def update(self, blocked: set):
        self.items = [f for f in self.items if not f.is_expired()]
        self.spawn(blocked)

    def pop_at(self, pos) -> FoodItem | None:
        for i, f in enumerate(self.items):
            if f.pos == pos:
                return self.items.pop(i)
        return None

    def draw(self, surface):
        for f in self.items:
            f.draw(surface)


# ─────────────────────────── Power-ups ──────────────────────────────────────

class PowerUp:
    SPEED  = "speed"
    SLOW   = "slow"
    SHIELD = "shield"

    LABELS = {SPEED: "⚡ SPEED", SLOW: "🐢 SLOW", SHIELD: "🛡 SHIELD"}
    COLORS = {SPEED: POWERUP_SPEED_COLOR,
              SLOW:  POWERUP_SLOW_COLOR,
              SHIELD: POWERUP_SHIELD_COLOR}

    def __init__(self, pos, kind):
        self.pos        = pos
        self.kind       = kind
        self.spawn_time = pygame.time.get_ticks()

    @property
    def color(self):
        return self.COLORS[self.kind]

    def is_expired(self) -> bool:
        return (pygame.time.get_ticks() - self.spawn_time) > POWERUP_FIELD_LIFE

    def draw(self, surface, cell_size=CELL_SIZE, hud_h=HUD_HEIGHT):
        cx, cy = self.pos
        rect   = pygame.Rect(cx * cell_size, hud_h + cy * cell_size,
                             cell_size, cell_size)
        t      = pygame.time.get_ticks() / 300
        r      = cell_size // 2 - 1
        color  = self.color
        # Rotating outline
        center = rect.center
        for angle_offset in range(0, 360, 90):
            angle = math.radians(t * 60 + angle_offset)
            px    = int(center[0] + r * math.cos(angle))
            py    = int(center[1] + r * math.sin(angle))
            pygame.draw.circle(surface, color, (px, py), 3)
        pygame.draw.circle(surface, color, center, r - 3)
        pygame.draw.circle(surface, WHITE, center, r - 5, 1)


class PowerUpManager:
    def __init__(self):
        self.item: PowerUp | None = None
        self.active_kind: str | None = None
        self.active_end:  int        = 0
        self.shield_ready: bool      = False
        self._next_spawn: int        = pygame.time.get_ticks() + 5000

    def blocked(self) -> set:
        return {self.item.pos} if self.item else set()

    def update(self, blocked: set):
        now = pygame.time.get_ticks()
        # Expire field item
        if self.item and self.item.is_expired():
            self.item = None
        # Expire active power-up
        if self.active_kind and self.active_kind != PowerUp.SHIELD and now > self.active_end:
            self.active_kind = None
        # Spawn new field item
        if self.item is None and now >= self._next_spawn:
            pos       = random_cell(blocked)
            kind      = random.choice([PowerUp.SPEED, PowerUp.SLOW, PowerUp.SHIELD])
            self.item = PowerUp(pos, kind)
            self._next_spawn = now + random.randint(8000, 15000)

    def collect(self, pos) -> str | None:
        if self.item and self.item.pos == pos:
            kind      = self.item.kind
            self.item = None
            now       = pygame.time.get_ticks()
            if kind == PowerUp.SHIELD:
                self.active_kind  = PowerUp.SHIELD
                self.shield_ready = True
            else:
                self.active_kind = kind
                self.active_end  = now + POWERUP_DURATION
            return kind
        return None

    def use_shield(self) -> bool:
        """Returns True and disables shield if active."""
        if self.active_kind == PowerUp.SHIELD and self.shield_ready:
            self.active_kind  = None
            self.shield_ready = False
            return True
        return False

    @property
    def current_speed(self) -> int:
        if self.active_kind == PowerUp.SPEED:
            return SPEED_BOOST
        if self.active_kind == PowerUp.SLOW:
            return SPEED_SLOW
        return SPEED_NORMAL

    def draw(self, surface):
        if self.item:
            self.item.draw(surface)

    def hud_text(self) -> str:
        if not self.active_kind:
            return ""
        if self.active_kind == PowerUp.SHIELD:
            return "🛡 SHIELD"
        remaining = max(0, self.active_end - pygame.time.get_ticks()) // 1000
        return f"{PowerUp.LABELS[self.active_kind]} {remaining}s"


# ─────────────────────────── Obstacles ──────────────────────────────────────

class ObstacleManager:
    def __init__(self):
        self.cells: set = set()

    def generate(self, level: int, snake_cells: set, food_cells: set,
                 powerup_cells: set):
        if level < OBSTACLES_START_LEVEL:
            self.cells = set()
            return
        count = (level - OBSTACLES_START_LEVEL + 1) * OBSTACLES_PER_LEVEL
        avoid = snake_cells | food_cells | powerup_cells
        # Expand avoid zone around snake head by 3 cells
        if snake_cells:
            hx, hy = next(iter(snake_cells))
            for dx in range(-3, 4):
                for dy in range(-3, 4):
                    avoid.add((hx + dx, hy + dy))
        new_cells = set()
        attempts  = 0
        while len(new_cells) < count and attempts < count * 10:
            cell = random_cell(avoid | new_cells)
            new_cells.add(cell)
            attempts += 1
        self.cells = new_cells

    def has(self, pos) -> bool:
        return pos in self.cells

    def draw(self, surface, cell_size=CELL_SIZE, hud_h=HUD_HEIGHT):
        for cx, cy in self.cells:
            rect = pygame.Rect(cx * cell_size, hud_h + cy * cell_size,
                               cell_size, cell_size)
            pygame.draw.rect(surface, OBSTACLE_COLOR, rect, border_radius=2)
            pygame.draw.rect(surface, GRAY, rect.inflate(-4, -4), 1,
                             border_radius=2)


# ─────────────────────────── HUD ────────────────────────────────────────────

class HUD:
    def __init__(self, font_large, font_small):
        self.font_large = font_large
        self.font_small = font_small

    def draw(self, surface, score, level, personal_best, powerup_text,
             shield_active, db_ok):
        # Background bar
        rect = pygame.Rect(0, 0, WINDOW_WIDTH, HUD_HEIGHT)
        pygame.draw.rect(surface, HUD_BG, rect)
        pygame.draw.line(surface, GRAY, (0, HUD_HEIGHT), (WINDOW_WIDTH, HUD_HEIGHT), 1)

        # Score
        s = self.font_large.render(f"SCORE  {score}", True, WHITE)
        surface.blit(s, (20, 12))

        # Level
        l = self.font_small.render(f"LVL {level}", True, ACCENT)
        surface.blit(l, (20, 44))

        # Personal best
        pb = self.font_small.render(f"BEST {personal_best}", True, GOLD)
        surface.blit(pb, (160, 44))

        # Power-up status
        if powerup_text:
            color = PURPLE if "SHIELD" in powerup_text else ORANGE
            pt = self.font_small.render(powerup_text, True, color)
            surface.blit(pt, (WINDOW_WIDTH // 2 - pt.get_width() // 2, 28))

        # DB indicator
        dot_color = GREEN if db_ok else RED
        pygame.draw.circle(surface, dot_color,
                           (WINDOW_WIDTH - 15, HUD_HEIGHT // 2), 5)


# ─────────────────────────── Grid overlay ───────────────────────────────────

def draw_grid(surface):
    for col in range(COLS + 1):
        x = col * CELL_SIZE
        pygame.draw.line(surface, (35, 35, 50),
                         (x, HUD_HEIGHT), (x, WINDOW_HEIGHT), 1)
    for row in range(ROWS + 1):
        y = HUD_HEIGHT + row * CELL_SIZE
        pygame.draw.line(surface, (35, 35, 50),
                         (0, y), (WINDOW_WIDTH, y), 1)


# ─────────────────────────── Main GameSession ────────────────────────────────

class GameSession:
    """Encapsulates one play session."""

    def __init__(self, settings: dict, personal_best: int, db_ok: bool):
        self.settings      = settings
        self.personal_best = personal_best
        self.db_ok         = db_ok

        snake_color = tuple(settings.get("snake_color", list(GREEN)))

        self.snake    = Snake(color=snake_color)
        self.food_mgr = FoodManager()
        self.pu_mgr   = PowerUpManager()
        self.obs_mgr  = ObstacleManager()

        self.score        = 0
        self.level        = 1
        self.move_timer   = 0
        self.game_over    = False
        self.death_reason = ""
        self.flash_timer  = 0   # ms to flash effect

        # Initial spawns
        self.food_mgr.spawn(self.snake.occupies())

        # Fonts (created here, shared with HUD)
        pygame.font.init()
        self.font_lg = pygame.font.SysFont("monospace", 22, bold=True)
        self.font_sm = pygame.font.SysFont("monospace", 16)
        self.hud     = HUD(self.font_lg, self.font_sm)

    # ── helpers ──────────────────────────────────────────────────────────────

    def _all_blocked(self) -> set:
        return (self.snake.occupies() |
                self.food_mgr.blocked() |
                self.pu_mgr.blocked()  |
                self.obs_mgr.cells)

    def _check_level_up(self):
        new_level = self.score // LEVEL_SCORE_THRESHOLD + 1
        if new_level > self.level:
            self.level = new_level
            self.obs_mgr.generate(
                self.level,
                self.snake.occupies(),
                self.food_mgr.blocked(),
                self.pu_mgr.blocked()
            )
            self.flash_timer = 800

    # ── per-frame update ─────────────────────────────────────────────────────

    def update(self, dt: int):
        if self.game_over:
            return

        self.move_timer += dt
        speed = self.pu_mgr.current_speed

        if self.move_timer < speed:
            return
        self.move_timer = 0

        # Move
        self.snake.move()
        head = self.snake.head

        # Wall collision
        if self.snake.wall_collision():
            if self.pu_mgr.use_shield():
                # Wrap around (shield saves once)
                hx = head[0] % COLS
                hy = head[1] % ROWS
                self.snake.body[0] = (hx, hy)
            else:
                self.game_over    = True
                self.death_reason = "Hit the wall"
                return

        # Obstacle collision
        if self.obs_mgr.has(head):
            if self.pu_mgr.use_shield():
                pass  # shield absorbs
            else:
                self.game_over    = True
                self.death_reason = "Hit an obstacle"
                return

        # Self collision
        if self.snake.self_collision():
            if self.pu_mgr.use_shield():
                pass
            else:
                self.game_over    = True
                self.death_reason = "Bit yourself"
                return

        # Food
        food = self.food_mgr.pop_at(head)
        if food:
            if food.kind == FoodItem.POISON:
                if not self.snake.shorten(2):
                    self.game_over    = True
                    self.death_reason = "Ate poison"
                    return
            else:
                self.snake.grow(1)
                self.score += food.points
                self._check_level_up()

        # Power-up
        self.pu_mgr.collect(head)

        # Update managers
        blocked = self._all_blocked()
        self.food_mgr.update(blocked)
        self.pu_mgr.update(blocked)

        if self.flash_timer > 0:
            self.flash_timer -= dt

    # ── handle key ───────────────────────────────────────────────────────────

    def handle_key(self, key):
        mapping = {
            pygame.K_UP:    (0, -1), pygame.K_w: (0, -1),
            pygame.K_DOWN:  (0,  1), pygame.K_s: (0,  1),
            pygame.K_LEFT:  (-1, 0), pygame.K_a: (-1, 0),
            pygame.K_RIGHT: (1,  0), pygame.K_d: (1,  0),
        }
        if key in mapping:
            dx, dy = mapping[key]
            self.snake.set_direction(dx, dy)

    # ── draw ─────────────────────────────────────────────────────────────────

    def draw(self, surface):
        # Background
        surface.fill(DARK_BG)

        # Grid
        if self.settings.get("grid_overlay", False):
            draw_grid(surface)

        # Flash on level-up
        if self.flash_timer > 0:
            flash_surf = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            alpha      = int(60 * (self.flash_timer / 800))
            flash_surf.fill((255, 255, 100, alpha))
            surface.blit(flash_surf, (0, 0))

        # Game objects
        self.obs_mgr.draw(surface)
        self.food_mgr.draw(surface)
        self.pu_mgr.draw(surface)
        self.snake.draw(surface)

        # HUD
        self.hud.draw(
            surface, self.score, self.level, self.personal_best,
            self.pu_mgr.hud_text(),
            self.pu_mgr.active_kind == PowerUp.SHIELD,
            self.db_ok
        )