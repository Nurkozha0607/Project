# main.py — Entry point: screen manager, all game screens

import pygame
import sys
import json
import os

from config import *
import db
from game import GameSession

# ─────────────────────────── Settings I/O ───────────────────────────────────

SETTINGS_PATH = os.path.join(os.path.dirname(__file__), "settings.json")

DEFAULT_SETTINGS = {
    "snake_color": list(GREEN),
    "grid_overlay": False,
    "sound": True,
}

def load_settings() -> dict:
    try:
        with open(SETTINGS_PATH) as f:
            data = json.load(f)
            for k, v in DEFAULT_SETTINGS.items():
                data.setdefault(k, v)
            return data
    except Exception:
        return dict(DEFAULT_SETTINGS)

def save_settings(settings: dict):
    try:
        with open(SETTINGS_PATH, "w") as f:
            json.dump(settings, f, indent=4)
    except Exception:
        pass


# ─────────────────────────── UI helpers ─────────────────────────────────────

def draw_bg(surface):
    surface.fill(DARK_BG)
    # Subtle dots pattern
    for x in range(0, WINDOW_WIDTH, 40):
        for y in range(0, WINDOW_HEIGHT, 40):
            pygame.draw.circle(surface, (30, 30, 48), (x, y), 1)


def draw_panel(surface, rect, radius=12):
    panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(panel, (*PANEL_BG, 230), panel.get_rect(), border_radius=radius)
    pygame.draw.rect(panel, (*GRAY, 120), panel.get_rect(), 1, border_radius=radius)
    surface.blit(panel, rect.topleft)


class Button:
    def __init__(self, rect, text, font,
                 color=ACCENT, text_color=DARK_BG,
                 hover_color=None, inactive_color=None):
        self.rect         = pygame.Rect(rect)
        self.text         = text
        self.font         = font
        self.color        = color
        self.text_color   = text_color
        self.hover_color  = hover_color or tuple(min(255, c + 40) for c in color)
        self.inactive_color = inactive_color or color
        self._hovered     = False

    def handle_event(self, event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self._hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False

    def draw(self, surface):
        color = self.hover_color if self._hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        if self._hovered:
            pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=8)
        label = self.font.render(self.text, True, self.text_color)
        surface.blit(label, label.get_rect(center=self.rect.center))


class TextInput:
    def __init__(self, rect, font, prompt="", max_len=16):
        self.rect    = pygame.Rect(rect)
        self.font    = font
        self.prompt  = prompt
        self.max_len = max_len
        self.text    = ""
        self.active  = True
        self._cursor_vis = True
        self._cursor_timer = 0

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return True
            elif len(self.text) < self.max_len and event.unicode.isprintable():
                self.text += event.unicode
        return False

    def update(self, dt):
        self._cursor_timer += dt
        if self._cursor_timer > 500:
            self._cursor_vis   = not self._cursor_vis
            self._cursor_timer = 0

    def draw(self, surface):
        pygame.draw.rect(surface, PANEL_BG, self.rect, border_radius=6)
        border_color = ACCENT if self.active else GRAY
        pygame.draw.rect(surface, border_color, self.rect, 2, border_radius=6)
        display = self.text + ("|" if self._cursor_vis else " ")
        label   = self.font.render(display, True, WHITE)
        surface.blit(label, label.get_rect(midleft=(self.rect.left + 12,
                                                     self.rect.centery)))
        if not self.text:
            ph = self.font.render(self.prompt, True, GRAY)
            surface.blit(ph, ph.get_rect(midleft=(self.rect.left + 12,
                                                   self.rect.centery)))


# ─────────────────────────── Screen base ────────────────────────────────────

class Screen:
    def __init__(self, app):
        self.app = app

    def handle_event(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self, surface):
        pass


# ─────────────────────────── Main Menu ──────────────────────────────────────

class MainMenuScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        f_title = pygame.font.SysFont("monospace", 52, bold=True)
        f_sub   = pygame.font.SysFont("monospace", 20)
        f_btn   = pygame.font.SysFont("monospace", 18, bold=True)

        self.title_surf = f_title.render("🐍 SNAKE", True, GREEN)
        self.sub_surf   = f_sub.render("TSIS 3 — Advanced Edition", True, GRAY)

        cw = 300
        cx = WINDOW_WIDTH // 2 - cw // 2
        self.username_input = TextInput(
            pygame.Rect(cx, 240, cw, 42), f_sub,
            prompt="Enter username…", max_len=20
        )
        self.username_input.text = app.username

        self.buttons = [
            Button((cx, 310, cw, 46), "▶  PLAY",        f_btn),
            Button((cx, 368, cw, 46), "🏆  LEADERBOARD", f_btn, color=GOLD,    text_color=DARK_BG),
            Button((cx, 426, cw, 46), "⚙  SETTINGS",    f_btn, color=PURPLE,  text_color=WHITE),
            Button((cx, 484, cw, 46), "✕  QUIT",         f_btn, color=DARK_RED, text_color=WHITE),
        ]
        self.db_font = pygame.font.SysFont("monospace", 13)

    def handle_event(self, event):
        self.username_input.handle_event(event)
        self.app.username = self.username_input.text

        actions = ["play", "leaderboard", "settings", "quit"]
        for btn, action in zip(self.buttons, actions):
            if btn.handle_event(event):
                if action == "play":
                    name = self.app.username.strip() or "Player"
                    self.app.username = name
                    self.app.go_play()
                elif action == "leaderboard":
                    self.app.set_screen("leaderboard")
                elif action == "settings":
                    self.app.set_screen("settings")
                elif action == "quit":
                    pygame.quit(); sys.exit()

    def update(self, dt):
        self.username_input.update(dt)

    def draw(self, surface):
        draw_bg(surface)

        # Title
        ty = 80
        surface.blit(self.title_surf,
                     self.title_surf.get_rect(centerx=WINDOW_WIDTH // 2, top=ty))
        surface.blit(self.sub_surf,
                     self.sub_surf.get_rect(centerx=WINDOW_WIDTH // 2, top=ty + 70))

        # Username label
        f = pygame.font.SysFont("monospace", 15)
        lbl = f.render("USERNAME", True, ACCENT)
        surface.blit(lbl, (WINDOW_WIDTH // 2 - lbl.get_width() // 2, 218))

        self.username_input.draw(surface)
        for btn in self.buttons:
            btn.draw(surface)

        # DB status
        status = "● DB connected" if self.app.db_ok else "● DB offline (scores won't save)"
        col    = GREEN if self.app.db_ok else DARK_RED
        st     = self.db_font.render(status, True, col)
        surface.blit(st, st.get_rect(centerx=WINDOW_WIDTH // 2,
                                      bottom=WINDOW_HEIGHT - 10))


# ─────────────────────────── Game Screen ────────────────────────────────────

class GameScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        personal_best = (db.get_personal_best(app.username)
                         if app.db_ok else 0)
        self.session  = GameSession(app.settings, personal_best, app.db_ok)
        self._pause   = False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.app.set_screen("menu")
            elif event.key == pygame.K_p:
                self._pause = not self._pause
            else:
                self.session.handle_key(event.key)

    def update(self, dt):
        if self._pause:
            return
        self.session.update(dt)
        if self.session.game_over:
            # Save score
            if self.app.db_ok:
                db.save_score(self.app.username,
                              self.session.score,
                              self.session.level)
            self.app.set_screen("gameover",
                                score=self.session.score,
                                level=self.session.level,
                                reason=self.session.death_reason)

    def draw(self, surface):
        self.session.draw(surface)
        if self._pause:
            f = pygame.font.SysFont("monospace", 36, bold=True)
            t = f.render("PAUSED", True, WHITE)
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            surface.blit(overlay, (0, 0))
            surface.blit(t, t.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)))


# ─────────────────────────── Game Over ──────────────────────────────────────

class GameOverScreen(Screen):
    def __init__(self, app, score=0, level=1, reason=""):
        super().__init__(app)
        self.score  = score
        self.level  = level
        self.reason = reason
        self.pb     = db.get_personal_best(app.username) if app.db_ok else score
        self.is_new_pb = (score >= self.pb)

        f_big  = pygame.font.SysFont("monospace", 40, bold=True)
        f_med  = pygame.font.SysFont("monospace", 22)
        f_btn  = pygame.font.SysFont("monospace", 18, bold=True)

        self.f_big = f_big
        self.f_med = f_med

        cw = 340
        cx = WINDOW_WIDTH // 2 - cw // 2
        self.buttons = [
            Button((cx, 420, cw, 50), "↺  RETRY",     f_btn),
            Button((cx, 484, cw, 50), "⌂  MAIN MENU", f_btn, color=GRAY, text_color=WHITE),
        ]

    def handle_event(self, event):
        actions = ["retry", "menu"]
        for btn, action in zip(self.buttons, actions):
            if btn.handle_event(event):
                if action == "retry":
                    self.app.go_play()
                else:
                    self.app.set_screen("menu")

    def draw(self, surface):
        draw_bg(surface)
        cw  = WINDOW_WIDTH // 2
        y   = 100

        title = self.f_big.render("GAME OVER", True, RED)
        surface.blit(title, title.get_rect(centerx=cw, top=y))

        if self.reason:
            r = self.f_med.render(self.reason, True, LIGHT_GRAY)
            surface.blit(r, r.get_rect(centerx=cw, top=y + 60))

        draw_panel(surface, pygame.Rect(cw - 160, y + 105, 320, 200))

        rows = [
            ("SCORE",        str(self.score),  WHITE),
            ("LEVEL REACHED", str(self.level), ACCENT),
            ("PERSONAL BEST", str(self.pb),    GOLD),
        ]
        for i, (label, val, col) in enumerate(rows):
            lbl = self.f_med.render(label, True, GRAY)
            val_s = self.f_med.render(val,  True, col)
            ry = y + 125 + i * 55
            surface.blit(lbl,  lbl.get_rect( left=cw - 140, top=ry))
            surface.blit(val_s, val_s.get_rect(right=cw + 140, top=ry))

        if self.is_new_pb:
            pb_f = pygame.font.SysFont("monospace", 18, bold=True)
            pb_t = pb_f.render("🏆 NEW PERSONAL BEST!", True, GOLD)
            surface.blit(pb_t, pb_t.get_rect(centerx=cw, top=y + 315))

        for btn in self.buttons:
            btn.draw(surface)


# ─────────────────────────── Leaderboard ────────────────────────────────────

class LeaderboardScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.rows     = db.get_top10() if app.db_ok else []
        f_btn         = pygame.font.SysFont("monospace", 18, bold=True)
        self.back_btn = Button((20, WINDOW_HEIGHT - 60, 120, 40), "← BACK", f_btn,
                               color=GRAY, text_color=WHITE)
        self.f_title  = pygame.font.SysFont("monospace", 32, bold=True)
        self.f_hdr    = pygame.font.SysFont("monospace", 15, bold=True)
        self.f_row    = pygame.font.SysFont("monospace", 15)

    def handle_event(self, event):
        if self.back_btn.handle_event(event):
            self.app.set_screen("menu")
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.set_screen("menu")

    def draw(self, surface):
        draw_bg(surface)
        cw = WINDOW_WIDTH // 2

        title = self.f_title.render("🏆 LEADERBOARD", True, GOLD)
        surface.blit(title, title.get_rect(centerx=cw, top=30))

        if not self.app.db_ok:
            msg = self.f_hdr.render("Database not connected", True, RED)
            surface.blit(msg, msg.get_rect(centerx=cw, top=100))
            self.back_btn.draw(surface)
            return

        # Table
        TABLE_LEFT  = 60
        TABLE_TOP   = 100
        ROW_H       = 38
        COLS_X      = [60, 110, 300, 460, 580]  # rank, name, score, level, date
        HEADERS     = ["#", "USERNAME", "SCORE", "LVL", "DATE"]

        draw_panel(surface, pygame.Rect(TABLE_LEFT - 10, TABLE_TOP - 10,
                                        WINDOW_WIDTH - 100, 38))
        for i, (hdr, x) in enumerate(zip(HEADERS, COLS_X)):
            h = self.f_hdr.render(hdr, True, ACCENT)
            surface.blit(h, (x, TABLE_TOP))

        for ri, row in enumerate(self.rows):
            ry = TABLE_TOP + 38 + ri * ROW_H
            if ri % 2 == 0:
                draw_panel(surface,
                           pygame.Rect(TABLE_LEFT - 10, ry - 4,
                                       WINDOW_WIDTH - 100, ROW_H - 2), radius=4)

            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(row["rank"], str(row["rank"]))
            color = {1: GOLD, 2: LIGHT_GRAY, 3: ORANGE}.get(row["rank"], WHITE)

            cells = [medal, row["username"], str(row["score"]),
                     str(row["level_reached"]), row["timestamp"]]
            for cell, x in zip(cells, COLS_X):
                s = self.f_row.render(str(cell), True, color)
                surface.blit(s, (x, ry + 4))

        self.back_btn.draw(surface)


# ─────────────────────────── Settings ───────────────────────────────────────

COLOR_PRESETS = [
    ("Green",    (60,  220, 100)),
    ("Cyan",     (60,  220, 220)),
    ("Yellow",   (240, 200,  40)),
    ("Orange",   (240, 140,  40)),
    ("Pink",     (240,  80, 160)),
    ("White",    (220, 220, 220)),
]

class SettingsScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.settings = dict(app.settings)
        f_btn  = pygame.font.SysFont("monospace", 18, bold=True)
        f_lbl  = pygame.font.SysFont("monospace", 18)
        self.f_lbl   = f_lbl
        self.f_title = pygame.font.SysFont("monospace", 32, bold=True)

        # Save & Back
        self.save_btn = Button((WINDOW_WIDTH // 2 - 150, 530, 300, 48),
                               "💾  SAVE & BACK", f_btn)

        # Color swatches
        swatch_y = 320
        swatch_w = 90
        swatch_h = 36
        total_w  = len(COLOR_PRESETS) * (swatch_w + 10) - 10
        swatch_x = WINDOW_WIDTH // 2 - total_w // 2
        self.swatch_rects = []
        for i, (name, color) in enumerate(COLOR_PRESETS):
            rect = pygame.Rect(swatch_x + i * (swatch_w + 10), swatch_y,
                               swatch_w, swatch_h)
            self.swatch_rects.append((rect, color, name))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.set_screen("menu")

        if self.save_btn.handle_event(event):
            self.app.settings = self.settings
            save_settings(self.settings)
            self.app.set_screen("menu")

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            # Grid toggle
            if self._grid_rect.collidepoint(mx, my):
                self.settings["grid_overlay"] = not self.settings["grid_overlay"]

            # Sound toggle
            if self._sound_rect.collidepoint(mx, my):
                self.settings["sound"] = not self.settings["sound"]

            # Color swatches
            for rect, color, _ in self.swatch_rects:
                if rect.collidepoint(mx, my):
                    self.settings["snake_color"] = list(color)

    def draw(self, surface):
        draw_bg(surface)
        cw = WINDOW_WIDTH // 2

        title = self.f_title.render("⚙ SETTINGS", True, ACCENT)
        surface.blit(title, title.get_rect(centerx=cw, top=40))

        panel = pygame.Rect(cw - 300, 110, 600, 400)
        draw_panel(surface, panel)

        # Grid toggle
        gy = 150
        self._grid_rect = pygame.Rect(cw + 80, gy, 100, 36)
        lbl = self.f_lbl.render("Grid Overlay", True, WHITE)
        surface.blit(lbl, (cw - 280, gy + 6))
        on = self.settings.get("grid_overlay", False)
        self._draw_toggle(surface, self._grid_rect, on)

        # Sound toggle
        sy = 220
        self._sound_rect = pygame.Rect(cw + 80, sy, 100, 36)
        lbl2 = self.f_lbl.render("Sound", True, WHITE)
        surface.blit(lbl2, (cw - 280, sy + 6))
        on2 = self.settings.get("sound", True)
        self._draw_toggle(surface, self._sound_rect, on2)

        # Snake color
        clbl = self.f_lbl.render("Snake Color", True, WHITE)
        surface.blit(clbl, clbl.get_rect(centerx=cw, top=282))

        cur_color = tuple(self.settings.get("snake_color", list(GREEN)))
        for rect, color, name in self.swatch_rects:
            pygame.draw.rect(surface, color, rect, border_radius=6)
            if tuple(color) == cur_color:
                pygame.draw.rect(surface, WHITE, rect, 3, border_radius=6)
            f_sm = pygame.font.SysFont("monospace", 11)
            lbl  = f_sm.render(name, True, DARK_BG)
            surface.blit(lbl, lbl.get_rect(center=rect.center))

        self.save_btn.draw(surface)

    def _draw_toggle(self, surface, rect, on):
        bg = GREEN if on else GRAY
        pygame.draw.rect(surface, bg, rect, border_radius=18)
        knob_x = rect.right - 20 if on else rect.left + 20
        pygame.draw.circle(surface, WHITE, (knob_x, rect.centery), 14)
        f = pygame.font.SysFont("monospace", 12, bold=True)
        label = f.render("ON" if on else "OFF", True, DARK_BG if on else WHITE)
        offset = -25 if on else 10
        surface.blit(label, label.get_rect(midleft=(rect.left + (10 if on else 40),
                                                     rect.centery)))


# ─────────────────────────── Application ────────────────────────────────────

class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.surface  = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock    = pygame.time.Clock()
        self.settings = load_settings()
        self.username = ""

        # DB init
        ok, err = db.init_db()
        self.db_ok = ok
        if not ok:
            print(f"[DB] Cannot connect: {err}")

        self.screen = MainMenuScreen(self)

    def set_screen(self, name: str, **kwargs):
        screens = {
            "menu":        lambda: MainMenuScreen(self),
            "leaderboard": lambda: LeaderboardScreen(self),
            "settings":    lambda: SettingsScreen(self),
            "gameover":    lambda: GameOverScreen(self, **kwargs),
        }
        self.screen = screens[name]()

    def go_play(self):
        self.screen = GameScreen(self)

    def run(self):
        while True:
            dt = self.clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                self.screen.handle_event(event)

            self.screen.update(dt)
            self.screen.draw(self.surface)
            pygame.display.flip()


# ─────────────────────────── Entry point ────────────────────────────────────

if __name__ == "__main__":
    App().run()