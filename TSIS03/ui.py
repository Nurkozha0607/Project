# ──────────────────────────────────────────────────────────────────────────────
# ui.py
# Responsible for: every non-gameplay screen and the in-game HUD.
# Contains pure drawing functions plus a lightweight Button helper so the
# rest of the code never needs to touch pygame.font / pygame.draw directly
# for UI elements.
# ──────────────────────────────────────────────────────────────────────────────

import pygame
from persistence import load_leaderboard

# ── Colors ────────────────────────────────────────────────────────────────────
BLACK       = (0,   0,   0  )
WHITE       = (255, 255, 255)
YELLOW      = (255, 215, 0  )
RED         = (220, 50,  50 )
GREEN       = (60,  200, 60 )
BLUE        = (60,  120, 220)
GRAY        = (80,  80,  80 )
DARK        = (20,  20,  30 )
PANEL       = (30,  30,  45, 200)   # semi-transparent panel
HIGHLIGHT   = (255, 200, 0  )
NITRO_COL   = (0,   200, 255)
SHIELD_COL  = (80,  80,  255)
REPAIR_COL  = (60,  220, 60 )

# ── Fonts (initialised once, reused everywhere) ───────────────────────────────
_fonts: dict = {}

def _font(size: int) -> pygame.font.Font:
    """Return a cached Impact font (fallback: default) at the given size."""
    if size not in _fonts:
        try:
            _fonts[size] = pygame.font.SysFont("impact", size)
        except Exception:
            _fonts[size] = pygame.font.SysFont(None, size)
    return _fonts[size]


# ── Utility ───────────────────────────────────────────────────────────────────

def draw_text(surface, text, size, color, cx, cy, shadow=True):
    """Render text centred at (cx, cy) with optional drop-shadow."""
    font   = _font(size)
    label  = font.render(str(text), True, color)
    rect   = label.get_rect(center=(cx, cy))
    if shadow:
        sh = font.render(str(text), True, BLACK)
        surface.blit(sh, (rect.x + 2, rect.y + 2))
    surface.blit(label, rect)
    return rect


def draw_text_left(surface, text, size, color, x, y, shadow=True):
    """Render text left-aligned at (x, y)."""
    font  = _font(size)
    label = font.render(str(text), True, color)
    if shadow:
        sh = font.render(str(text), True, BLACK)
        surface.blit(sh, (x + 2, y + 2))
    surface.blit(label, (x, y))


def overlay(surface, alpha=160):
    """Draw a full-screen dark overlay."""
    ov = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    ov.fill((0, 0, 0, alpha))
    surface.blit(ov, (0, 0))


def panel(surface, rect, color=PANEL):
    """Draw a rounded semi-transparent panel."""
    s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    s.fill(color)
    surface.blit(s, rect.topleft)
    pygame.draw.rect(surface, YELLOW, rect, 2, border_radius=10)


# ── Button ────────────────────────────────────────────────────────────────────

class Button:
    """
    A clickable rectangle button.
    Call .draw(surface) each frame and .is_clicked(event) on mouse events.
    """
    def __init__(self, cx, cy, w, h, text, color=GRAY, text_color=WHITE, font_size=26):
        self.rect       = pygame.Rect(0, 0, w, h)
        self.rect.center = (cx, cy)
        self.text        = text
        self.color       = color
        self.hover_color = tuple(min(c + 40, 255) for c in color)
        self.text_color  = text_color
        self.font_size   = font_size

    def draw(self, surface):
        mouse = pygame.mouse.get_pos()
        col   = self.hover_color if self.rect.collidepoint(mouse) else self.color
        pygame.draw.rect(surface, col, self.rect, border_radius=8)
        pygame.draw.rect(surface, YELLOW, self.rect, 2, border_radius=8)
        draw_text(surface, self.text, self.font_size, self.text_color,
                  self.rect.centerx, self.rect.centery, shadow=True)

    def is_clicked(self, event) -> bool:
        return (event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and self.rect.collidepoint(event.pos))


# ── Name Entry ────────────────────────────────────────────────────────────────

def draw_name_entry(surface, name: str, W: int, H: int):
    """
    Draw the name-entry screen.
    Returns nothing — the game loop drives input; this just paints the frame.
    """
    overlay(surface, 200)
    draw_text(surface, "STREET RACER", 56, YELLOW, W // 2, H // 2 - 160)
    draw_text(surface, "Enter your name:", 30, WHITE, W // 2, H // 2 - 80)

    # Input box
    box = pygame.Rect(W // 2 - 140, H // 2 - 28, 280, 52)
    pygame.draw.rect(surface, (40, 40, 60), box, border_radius=8)
    pygame.draw.rect(surface, YELLOW, box, 2, border_radius=8)
    draw_text(surface, name + "|", 30, WHITE, W // 2, H // 2)

    draw_text(surface, "Press ENTER to start", 22, (180, 180, 180), W // 2, H // 2 + 70)


# ── Main Menu ─────────────────────────────────────────────────────────────────

def build_main_menu_buttons(W: int, H: int) -> dict:
    """Return a dict of named Buttons for the main menu."""
    cx = W // 2
    return {
        "play":        Button(cx, H // 2 - 40, 220, 50, "▶  PLAY",       BLUE),
        "leaderboard": Button(cx, H // 2 + 25, 220, 50, "🏆  LEADERBOARD", GRAY),
        "settings":    Button(cx, H // 2 + 90, 220, 50, "⚙  SETTINGS",   GRAY),
        "quit":        Button(cx, H // 2 + 155, 220, 50, "✕  QUIT",       (120, 30, 30)),
    }


def draw_main_menu(surface, buttons: dict, street_img, W: int, H: int):
    """Draw the main menu over the street background."""
    surface.blit(street_img, (0, 0))
    overlay(surface, 160)
    draw_text(surface, "STREET RACER", 58, YELLOW, W // 2, H // 2 - 140)
    draw_text(surface, "ADVANCED EDITION", 24, (200, 200, 100), W // 2, H // 2 - 95)
    for btn in buttons.values():
        btn.draw(surface)


# ── Settings Screen ───────────────────────────────────────────────────────────

def build_settings_buttons(W: int, H: int, settings: dict) -> dict:
    """Build toggle/cycle buttons reflecting current settings."""
    cx = W // 2
    sound_label = "🔊 SOUND: ON" if settings["sound"] else "🔇 SOUND: OFF"
    color_label = f"🚗 CAR: {settings['car_color'].upper()}"
    diff_label  = f"⚡ DIFFICULTY: {settings['difficulty'].upper()}"
    return {
        "sound":      Button(cx, H // 2 - 80, 260, 48, sound_label),
        "car_color":  Button(cx, H // 2 - 10, 260, 48, color_label),
        "difficulty": Button(cx, H // 2 + 60, 260, 48, diff_label),
        "back":       Button(cx, H // 2 + 145, 200, 46, "← BACK", (80, 80, 80)),
    }


def draw_settings(surface, buttons: dict, W: int, H: int):
    """Draw the settings screen."""
    overlay(surface, 200)
    draw_text(surface, "SETTINGS", 48, YELLOW, W // 2, H // 2 - 160)
    for btn in buttons.values():
        btn.draw(surface)


# ── Leaderboard Screen ────────────────────────────────────────────────────────

def build_leaderboard_buttons(W: int, H: int) -> dict:
    return {"back": Button(W // 2, H - 55, 200, 44, "← BACK", (80, 80, 80))}


def draw_leaderboard(surface, buttons: dict, W: int, H: int):
    """Draw the top-10 leaderboard."""
    overlay(surface, 210)
    draw_text(surface, "🏆  LEADERBOARD", 46, YELLOW, W // 2, 55)

    board = load_leaderboard()
    headers = ("RANK", "NAME", "SCORE", "DIST", "COINS")
    cols    = (40, 110, 220, 305, 370)
    row_h   = 44
    top     = 110

    # Header row
    ph = pygame.Rect(20, top - 8, W - 40, row_h - 4)
    panel(surface, ph, (50, 50, 80, 180))
    for label, cx in zip(headers, cols):
        draw_text(surface, label, 20, YELLOW, cx, top + row_h // 2 - 10)

    if not board:
        draw_text(surface, "No scores yet — play a race!", 24,
                  (180, 180, 180), W // 2, top + 80)
    else:
        for i, entry in enumerate(board):
            y    = top + row_h + i * row_h
            bg   = (35, 35, 55, 160) if i % 2 == 0 else (45, 45, 70, 160)
            row  = pygame.Rect(20, y, W - 40, row_h - 2)
            panel(surface, row, bg)
            rank_col = YELLOW if i == 0 else WHITE
            vals = (f"#{i+1}", entry["name"][:10],
                    str(entry["score"]), f"{entry['distance']}m",
                    str(entry["coins"]))
            for val, cx in zip(vals, cols):
                draw_text(surface, val, 20, rank_col if i == 0 else WHITE, cx, y + row_h // 2 - 2)

    for btn in buttons.values():
        btn.draw(surface)


# ── Game-Over Screen ──────────────────────────────────────────────────────────

def build_gameover_buttons(W: int, H: int) -> dict:
    cx = W // 2
    return {
        "retry": Button(cx - 65, H // 2 + 120, 115, 46, "↺ RETRY", BLUE),
        "menu":  Button(cx + 65, H // 2 + 120, 115, 46, "⌂ MENU",  GRAY),
    }


def draw_game_over(surface, buttons: dict, score: int, distance: int,
                   coins: int, W: int, H: int):
    """Draw the game-over overlay."""
    overlay(surface, 185)
    cy = H // 2 - 80
    draw_text(surface, "GAME  OVER", 58, RED, W // 2, cy)
    draw_text(surface, f"SCORE    {score}",    28, WHITE,  W // 2, cy + 68)
    draw_text(surface, f"DISTANCE {distance}m", 28, WHITE, W // 2, cy + 100)
    draw_text(surface, f"COINS    {coins}",    28, YELLOW, W // 2, cy + 132)
    for btn in buttons.values():
        btn.draw(surface)


# ── In-game HUD ───────────────────────────────────────────────────────────────

def draw_hud(surface, player, score: int, level: int,
             distance: int, coin_img, powerup_state: dict, W: int, H: int):
    """
    Draw the in-game heads-up display.
    powerup_state = {"active": str|None, "timer": float}
    """
    # ── Top-left block: score / level / distance ──────────────────────────────
    draw_text_left(surface, f"SCORE  {score}",    20, WHITE,  8, 8)
    draw_text_left(surface, f"LVL    {level}",    20, GREEN,  8, 30)
    draw_text_left(surface, f"DIST   {distance}m",20, (180,220,255), 8, 52)

    # ── Top-right block: coin icon + count ────────────────────────────────────
    ci = pygame.transform.smoothscale(coin_img, (26, 26))
    surface.blit(ci, (W - 108, 8))
    draw_text_left(surface, f"x {player.coins}", 22, YELLOW, W - 78, 10)

    # ── Lives (bottom-left) ───────────────────────────────────────────────────
    from racer import PLAYER_IMGS
    life_img = pygame.transform.smoothscale(PLAYER_IMGS[player.color], (18, 34))
    for i in range(player.lives):
        surface.blit(life_img, (8 + i * 24, H - 44))

    # ── Active power-up indicator (top centre) ────────────────────────────────
    active = powerup_state.get("active")
    if active:
        timer   = powerup_state.get("timer", 0)
        pu_cols = {"nitro": NITRO_COL, "shield": SHIELD_COL, "repair": REPAIR_COL}
        pu_syms = {"nitro": "⚡NITRO", "shield": "🛡SHIELD", "repair": "🔧REPAIR"}
        col     = pu_cols.get(active, WHITE)
        label   = pu_syms.get(active, active.upper())
        bx      = pygame.Rect(W // 2 - 75, 6, 150, 28)
        panel(surface, bx, (20, 20, 40, 180))
        draw_text(surface, label, 18, col, W // 2, 20)
        if timer > 0:
            bar_w = int(144 * min(timer / 5.0, 1.0))
            pygame.draw.rect(surface, col, (W // 2 - 72, 34, bar_w, 6))
