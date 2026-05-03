# ──────────────────────────────────────────────────────────────────────────────
# racer.py
# Responsible for: every in-game entity and the physics / logic that drives
# them — Road, Player, Opponent (traffic), Obstacle (hazards), Coin, PowerUp.
# Also exposes the image constants that ui.py needs.
# ──────────────────────────────────────────────────────────────────────────────

import pygame
import random
import math
import os

# ── Asset path ────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR  = os.path.join(BASE_DIR, "assets")


def _load(filename, size=None) -> pygame.Surface:
    """Load an image from ASSETS_DIR with transparency; optionally resize."""
    path = os.path.join(ASSETS_DIR, filename)
    img  = pygame.image.load(path).convert_alpha()
    if size:
        img = pygame.transform.smoothscale(img, size)
    return img


# ── Shared image cache (loaded once) ─────────────────────────────────────────
# Populated by init_assets(); ui.py imports PLAYER_IMGS for life icons.
STREET_IMG  = None
COIN_IMG    = None
PLAYER_IMGS = {}   # {"blue": Surface, "red": Surface, ...}
OPP_IMG     = None


def init_assets():
    """Load all images into module-level cache. Call after pygame.init()."""
    global STREET_IMG, COIN_IMG, OPP_IMG

    SCREEN_W, SCREEN_H = pygame.display.get_surface().get_size()

    STREET_IMG = _load("image_street.png",  (SCREEN_W, SCREEN_H))
    COIN_IMG   = _load("image_coin.png",    (34, 34))
    OPP_IMG    = _load("image_player2.png", (68, 126))

    # Player tinted variants — start from the blue car and colorize
    base = _load("image_player1.png", (68, 126))
    tints = {
        "blue":   None,             # original
        "red":    (200, 60,  60 ),
        "green":  (60,  200, 60 ),
        "yellow": (220, 200, 0  ),
    }
    for color, tint in tints.items():
        if tint is None:
            PLAYER_IMGS[color] = base.copy()
        else:
            tinted = base.copy()
            tinted.fill((*tint, 0), special_flags=pygame.BLEND_RGBA_ADD)
            PLAYER_IMGS[color] = tinted


# ── Road layout ───────────────────────────────────────────────────────────────
ROAD_LEFT  = 60
ROAD_RIGHT = 340
NUM_LANES  = 2
LANE_W     = (ROAD_RIGHT - ROAD_LEFT) // NUM_LANES

def lane_center(lane: int) -> int:
    """Return the x-centre pixel of lane 0 or 1."""
    return ROAD_LEFT + lane * LANE_W + LANE_W // 2


# ── Colors ────────────────────────────────────────────────────────────────────
BLACK  = (0,   0,   0  )
YELLOW = (255, 215, 0  )
RED    = (200, 40,  40 )
ORANGE = (255, 140, 0  )
BROWN  = (100, 60,  20 )
CYAN   = (0,   200, 255)
PURPLE = (140, 0,   200)
GREEN  = (50,  200, 50 )


# ══════════════════════════════════════════════════════════════════════════════
# Road — infinite scrolling background
# ══════════════════════════════════════════════════════════════════════════════
class Road:
    """
    Uses two copies of the street image scrolled downward so the road looks
    infinite. Speed is updated externally by the game loop each level.
    """
    def __init__(self, H: int):
        self.H     = H
        self.y1    = 0
        self.y2    = -H
        self.speed = 5.0

    def update(self):
        self.y1 += self.speed
        self.y2 += self.speed
        if self.y1 >= self.H:  self.y1 = -self.H
        if self.y2 >= self.H:  self.y2 = -self.H

    def draw(self, surface):
        surface.blit(STREET_IMG, (0, int(self.y1)))
        surface.blit(STREET_IMG, (0, int(self.y2)))


# ══════════════════════════════════════════════════════════════════════════════
# Player
# ══════════════════════════════════════════════════════════════════════════════
class Player:
    """
    Human-controlled car. Supports:
      - 4-direction movement clamped to road boundaries
      - 3 lives with post-collision invincibility blink
      - Active power-up state (nitro / shield / repair)
      - Coin counter
    """
    BASE_SPEED = 5

    def __init__(self, color: str, W: int, H: int):
        self.color      = color
        self.image      = PLAYER_IMGS[color]
        self.W          = W
        self.H          = H
        self.w          = self.image.get_width()
        self.h          = self.image.get_height()
        self.x          = float(W // 2 - self.w // 2)
        self.y          = float(H - self.h - 30)
        self.speed      = self.BASE_SPEED
        self.lives      = 3
        self.coins      = 0
        self.invincible = 0     # countdown frames
        self.shield     = False # shield power-up active
        self.nitro_t    = 0.0   # nitro seconds remaining
        self.alive      = True

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def update(self, keys, dt_s: float):
        spd = self.speed * (1.8 if self.nitro_t > 0 else 1.0)

        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: self.x -= spd
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.x += spd
        if keys[pygame.K_UP]    or keys[pygame.K_w]: self.y -= spd
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: self.y += spd

        # Clamp inside road
        self.x = max(ROAD_LEFT, min(ROAD_RIGHT - self.w, self.x))
        self.y = max(0, min(self.H - self.h, self.y))

        if self.invincible > 0: self.invincible -= 1
        if self.nitro_t    > 0: self.nitro_t    -= dt_s

    def take_hit(self):
        """Process a collision. Returns True if the player is now dead."""
        if self.invincible > 0:
            return False
        if self.shield:
            self.shield     = False
            self.invincible = 60
            return False
        self.lives      -= 1
        self.invincible  = 90
        return self.lives <= 0

    def apply_powerup(self, kind: str):
        """Apply a collected power-up effect."""
        if kind == "nitro":
            self.nitro_t = 4.0
        elif kind == "shield":
            self.shield  = True
        elif kind == "repair":
            if self.lives < 3:
                self.lives += 1

    def draw(self, surface):
        # Blink while invincible
        if self.invincible % 6 < 3:
            img = self.image
            # Blue tint overlay when shield is active
            if self.shield:
                img = img.copy()
                img.fill((80, 80, 255, 60), special_flags=pygame.BLEND_RGBA_ADD)
            surface.blit(img, (int(self.x), int(self.y)))


# ══════════════════════════════════════════════════════════════════════════════
# Opponent (traffic car)
# ══════════════════════════════════════════════════════════════════════════════
class Opponent:
    """
    Downward-moving traffic car. Spawns above screen in a random lane at a
    safe distance from the player so it never appears on top of them.
    """
    def __init__(self, road_speed: float, level: int, player_y: float):
        self.image = OPP_IMG
        self.w     = self.image.get_width()
        self.h     = self.image.get_height()
        lane       = random.randint(0, NUM_LANES - 1)
        self.x     = lane_center(lane) - self.w // 2
        # Safe spawn: at least 2 car-heights above the player
        safe_top   = min(player_y - self.h * 2, -self.h)
        self.y     = float(safe_top - random.randint(0, 150))
        self.speed = random.uniform(0.8, 1.5 + level * 0.2)

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def update(self, road_speed: float):
        self.y += road_speed + self.speed

    def draw(self, surface):
        flipped = pygame.transform.flip(self.image, False, True)
        surface.blit(flipped, (int(self.x), int(self.y)))

    def off_screen(self, H: int) -> bool:
        return self.y > H + 60


# ══════════════════════════════════════════════════════════════════════════════
# Obstacle — road hazards (oil spill, barrier, pothole, speed bump, nitro strip)
# ══════════════════════════════════════════════════════════════════════════════
OBSTACLE_TYPES = ["oil", "barrier", "pothole", "speedbump", "nitrostrip"]

class Obstacle:
    """
    Static-ish road hazard that scrolls downward with the road.
    Each type has a different visual and gameplay effect:
      oil        — slide (slow / skid the player)
      barrier    — full stop / damage
      pothole    — damage
      speedbump  — briefly slow
      nitrostrip — free speed boost (road event, positive)
    """
    SIZES = {
        "oil":        (70, 40),
        "barrier":    (60, 22),
        "pothole":    (40, 30),
        "speedbump":  (80, 18),
        "nitrostrip": (80, 18),
    }
    COLORS = {
        "oil":        (20,  20,  20 ),
        "barrier":    (255, 80,  0  ),
        "pothole":    (50,  30,  10 ),
        "speedbump":  (200, 200, 0  ),
        "nitrostrip": (0,   220, 255),
    }

    def __init__(self, kind: str, player_y: float):
        self.kind  = kind
        self.w, self.h = self.SIZES[kind]
        lane   = random.randint(0, NUM_LANES - 1)
        cx     = lane_center(lane)
        self.x = float(cx - self.w // 2)
        safe_top = min(player_y - self.h * 3, -self.h)
        self.y   = float(safe_top - random.randint(0, 200))

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def update(self, road_speed: float):
        self.y += road_speed

    def draw(self, surface):
        col = self.COLORS[self.kind]
        r   = self.rect
        if self.kind == "oil":
            pygame.draw.ellipse(surface, col, r)
            pygame.draw.ellipse(surface, (40, 40, 40), r, 2)
        elif self.kind == "barrier":
            pygame.draw.rect(surface, col, r, border_radius=4)
            pygame.draw.rect(surface, BLACK, r, 2, border_radius=4)
            # Diagonal warning stripes
            for i in range(0, r.width, 14):
                sx = r.x + i
                pygame.draw.line(surface, BLACK,
                                 (sx, r.y), (sx + 10, r.y + r.height), 3)
        elif self.kind == "pothole":
            pygame.draw.ellipse(surface, col, r)
            pygame.draw.ellipse(surface, (80, 50, 20), r, 2)
        elif self.kind == "speedbump":
            pygame.draw.rect(surface, col, r, border_radius=6)
        elif self.kind == "nitrostrip":
            pygame.draw.rect(surface, col, r, border_radius=4)
            # Lightning bolt symbol
            mx, my = r.centerx, r.centery
            pts = [(mx-5, my-7),(mx+2, my-7),(mx-2, my),(mx+5, my),(mx-3, my+7),(mx+1, my)]
            pygame.draw.polygon(surface, YELLOW, pts)

    def off_screen(self, H: int) -> bool:
        return self.y > H + 60


# ══════════════════════════════════════════════════════════════════════════════
# Coin
# ══════════════════════════════════════════════════════════════════════════════
class Coin:
    """Gold coin collectible. Scrolls with the road; bobs up and down."""

    def __init__(self, player_y: float):
        self.w, self.h = COIN_IMG.get_size()
        self.x   = float(random.randint(ROAD_LEFT + 10, ROAD_RIGHT - self.w - 10))
        safe_top = min(player_y - self.h * 2, -self.h)
        self.y   = float(safe_top - random.randint(0, 250))
        self.bob = random.uniform(0, math.pi * 2)

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def update(self, road_speed: float):
        self.y   += road_speed * 0.9
        self.bob += 0.1

    def draw(self, surface):
        offset = int(4 * abs(math.sin(self.bob)))
        surface.blit(COIN_IMG, (int(self.x), int(self.y) + offset))

    def off_screen(self, H: int) -> bool:
        return self.y > H + 60


# ══════════════════════════════════════════════════════════════════════════════
# PowerUp
# ══════════════════════════════════════════════════════════════════════════════
PU_COLORS = {"nitro": CYAN, "shield": PURPLE, "repair": GREEN}
PU_SYMS   = {"nitro": "⚡", "shield": "🛡", "repair": "🔧"}
PU_TIMEOUT = 8.0   # seconds before a power-up disappears if not collected

class PowerUp:
    """
    Collectible power-up box. Scrolls with the road; pulses visually.
    Disappears after PU_TIMEOUT seconds even if not collected.
    Only one of each kind active at a time (enforced by the game loop).
    """
    SIZE = 36

    def __init__(self, kind: str, player_y: float):
        self.kind    = kind
        self.w = self.h = self.SIZE
        lane     = random.randint(0, NUM_LANES - 1)
        self.x   = float(lane_center(lane) - self.SIZE // 2)
        safe_top = min(player_y - self.h * 3, -self.h)
        self.y   = float(safe_top - random.randint(0, 200))
        self.age = 0.0      # seconds alive
        self.pulse = 0.0

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def update(self, road_speed: float, dt_s: float):
        self.y     += road_speed * 0.85
        self.age   += dt_s
        self.pulse += 0.12

    def expired(self) -> bool:
        return self.age >= PU_TIMEOUT

    def off_screen(self, H: int) -> bool:
        return self.y > H + 60

    def draw(self, surface):
        col   = PU_COLORS[self.kind]
        alpha = int(180 + 75 * math.sin(self.pulse))
        alpha = max(60, min(255, alpha))
        r     = self.rect

        # Pulsing background square
        s = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        s.fill((*col, alpha))
        surface.blit(s, r.topleft)
        pygame.draw.rect(surface, col, r, 2, border_radius=6)

        # Symbol (fallback: letter if emoji rendering fails)
        try:
            sym_font = pygame.font.SysFont("segoeuiemoji,applesymbol,symbola", 20)
        except Exception:
            sym_font = pygame.font.SysFont(None, 22)
        sym  = PU_SYMS.get(self.kind, self.kind[0].upper())
        lbl  = sym_font.render(sym, True, (255, 255, 255))
        surface.blit(lbl, lbl.get_rect(center=r.center))
