# ──────────────────────────────────────────────────────────────────────────────
# main.py
# Responsible for: the top-level game loop and state machine.
# States: NAME_ENTRY → MAIN_MENU → PLAYING → GAME_OVER → LEADERBOARD / SETTINGS
# Delegates all drawing to ui.py and all entity logic to racer.py.
# Persists scores and settings via persistence.py.
# ──────────────────────────────────────────────────────────────────────────────

import pygame
import random
import sys

from persistence import load_settings, save_settings, save_score
import racer
from racer import (Road, Player, Opponent, Obstacle, Coin, PowerUp,
                   OBSTACLE_TYPES, lane_center)
import ui
from ui import (Button,
                draw_name_entry,
                build_main_menu_buttons, draw_main_menu,
                build_settings_buttons,  draw_settings,
                build_leaderboard_buttons, draw_leaderboard,
                build_gameover_buttons,  draw_game_over,
                draw_hud)

# ── Window ────────────────────────────────────────────────────────────────────
W, H = 400, 700
FPS  = 60

pygame.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("🏁 Street Racer — Advanced Edition")
clock = pygame.time.Clock()

# ── Load assets & settings ────────────────────────────────────────────────────
racer.init_assets()          # populates STREET_IMG, COIN_IMG, PLAYER_IMGS, OPP_IMG
settings = load_settings()

# ── Difficulty presets ────────────────────────────────────────────────────────
DIFF = {
    "easy":   {"base_speed": 4.0, "opp_min": 80, "obs_min": 120, "score_mult": 0.8},
    "normal": {"base_speed": 5.0, "opp_min": 60, "obs_min": 90,  "score_mult": 1.0},
    "hard":   {"base_speed": 6.5, "opp_min": 40, "obs_min": 65,  "score_mult": 1.3},
}


# ══════════════════════════════════════════════════════════════════════════════
# Helper: reset / build a fresh game session
# ══════════════════════════════════════════════════════════════════════════════
def new_game(settings: dict):
    diff_key = settings.get("difficulty", "normal")
    d        = DIFF[diff_key]
    road     = Road(H)
    road.speed = d["base_speed"]
    player   = Player(settings.get("car_color", "blue"), W, H)
    return {
        "road":        road,
        "player":      player,
        "opponents":   [],
        "obstacles":   [],
        "coins":       [],
        "powerups":    [],
        "score":       0,
        "distance":    0.0,
        "level":       1,
        "opp_timer":   0,
        "obs_timer":   0,
        "coin_timer":  0,
        "pu_timer":    0,
        "powerup_state": {"active": None, "timer": 0.0},
        "diff":        d,
        "diff_key":    diff_key,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Spawning helpers
# ══════════════════════════════════════════════════════════════════════════════
def spawn_opponent(g):
    """Add a new traffic car if safe."""
    g["opponents"].append(Opponent(g["road"].speed, g["level"], g["player"].y))


def spawn_obstacle(g):
    """Add a random road obstacle."""
    kind = random.choice(OBSTACLE_TYPES)
    g["obstacles"].append(Obstacle(kind, g["player"].y))


def spawn_coin(g):
    g["coins"].append(Coin(g["player"].y))


def spawn_powerup(g):
    """Spawn a power-up only if that kind isn't already on screen."""
    active_kinds = {p.kind for p in g["powerups"]}
    available    = [k for k in ("nitro", "shield", "repair") if k not in active_kinds]
    if available:
        kind = random.choice(available)
        g["powerups"].append(PowerUp(kind, g["player"].y))


# ══════════════════════════════════════════════════════════════════════════════
# Main game-update tick (called every frame while STATE == "playing")
# ══════════════════════════════════════════════════════════════════════════════
def update_game(g, keys, dt_s: float) -> bool:
    """
    Advance one frame of gameplay.
    Returns True if the player just died (triggers game-over transition).
    """
    road   = g["road"]
    player = g["player"]
    diff   = g["diff"]
    level  = g["level"]

    # ── Score & level ─────────────────────────────────────────────────────────
    g["score"]    += int(1 * diff["score_mult"])
    g["distance"] += road.speed / 60.0   # metres at 60 FPS
    g["level"]     = 1 + int(g["score"] // 800)

    # Road speed scales with level
    road.speed = diff["base_speed"] + (level - 1) * 0.6

    # ── Update entities ───────────────────────────────────────────────────────
    road.update()
    player.update(keys, dt_s)

    # ── Spawn timers ──────────────────────────────────────────────────────────
    opp_interval  = max(diff["opp_min"] - level * 3, 22)
    obs_interval  = max(diff["obs_min"] - level * 4, 30)
    coin_interval = 75
    pu_interval   = 220

    g["opp_timer"]  += 1
    g["obs_timer"]  += 1
    g["coin_timer"] += 1
    g["pu_timer"]   += 1

    if g["opp_timer"]  >= opp_interval:  g["opp_timer"]  = 0; spawn_opponent(g)
    if g["obs_timer"]  >= obs_interval:  g["obs_timer"]  = 0; spawn_obstacle(g)
    if g["coin_timer"] >= coin_interval: g["coin_timer"] = 0; spawn_coin(g)
    if g["pu_timer"]   >= pu_interval:   g["pu_timer"]   = 0; spawn_powerup(g)

    # ── Update & cull opponents ───────────────────────────────────────────────
    for opp in g["opponents"][:]:
        opp.update(road.speed)
        if opp.off_screen(H):
            g["opponents"].remove(opp)
            continue
        if player.rect.colliderect(opp.rect):
            if player.take_hit():
                return True   # player dead

    # ── Update & cull obstacles ───────────────────────────────────────────────
    for obs in g["obstacles"][:]:
        obs.update(road.speed)
        if obs.off_screen(H):
            g["obstacles"].remove(obs)
            continue
        if player.rect.colliderect(obs.rect):
            if obs.kind == "nitrostrip":
                # Positive road event: free nitro boost
                player.nitro_t = 2.5
                g["obstacles"].remove(obs)
            elif obs.kind in ("oil", "speedbump"):
                # Slow-down hazard — just slide, no life lost
                player.speed = max(2, player.BASE_SPEED - 2)
                pygame.time.set_timer(pygame.USEREVENT + 1, 1500)
                g["obstacles"].remove(obs)
            else:
                # Damaging obstacle
                if player.take_hit():
                    return True
                g["obstacles"].remove(obs)

    # Restore speed after slow-down (handled via timer event in main loop)

    # ── Update & cull coins ───────────────────────────────────────────────────
    for coin in g["coins"][:]:
        coin.update(road.speed)
        if coin.off_screen(H):
            g["coins"].remove(coin)
            continue
        if player.rect.colliderect(coin.rect):
            player.coins += 1
            g["score"]   += int(50 * diff["score_mult"])
            g["coins"].remove(coin)

    # ── Update & cull power-ups ───────────────────────────────────────────────
    ps = g["powerup_state"]
    for pu in g["powerups"][:]:
        pu.update(road.speed, dt_s)
        if pu.off_screen(H) or pu.expired():
            g["powerups"].remove(pu)
            continue
        if player.rect.colliderect(pu.rect):
            # Only apply if no power-up currently active (or same kind)
            if ps["active"] is None or ps["active"] == pu.kind:
                player.apply_powerup(pu.kind)
                if pu.kind == "nitro":
                    ps["active"] = "nitro"
                    ps["timer"]  = 4.0
                elif pu.kind == "shield":
                    ps["active"] = "shield"
                    ps["timer"]  = -1   # until hit
                elif pu.kind == "repair":
                    ps["active"] = "repair"
                    ps["timer"]  = 0.5  # brief flash
                g["score"] += int(100 * diff["score_mult"])
                g["powerups"].remove(pu)

    # Tick power-up timer
    if ps["active"]:
        if ps["timer"] > 0:
            ps["timer"] -= dt_s
        if ps["active"] == "nitro" and ps["timer"] <= 0:
            ps["active"] = None
        elif ps["active"] == "shield" and not player.shield:
            ps["active"] = None
        elif ps["active"] == "repair" and ps["timer"] <= 0:
            ps["active"] = None

    return False   # player still alive


# ══════════════════════════════════════════════════════════════════════════════
# Draw game scene
# ══════════════════════════════════════════════════════════════════════════════
def draw_game(g):
    g["road"].draw(screen)
    for coin  in g["coins"]:     coin.draw(screen)
    for obs   in g["obstacles"]: obs.draw(screen)
    for pu    in g["powerups"]:  pu.draw(screen)
    for opp   in g["opponents"]: opp.draw(screen)
    g["player"].draw(screen)
    draw_hud(screen, g["player"], g["score"], g["level"],
             int(g["distance"]), racer.COIN_IMG,
             g["powerup_state"], W, H)


# ══════════════════════════════════════════════════════════════════════════════
# STATE MACHINE
# ══════════════════════════════════════════════════════════════════════════════
STATE    = "name_entry"
name     = ""
game     = None       # current game session dict
go_btns  = None       # game-over buttons
menu_btns    = build_main_menu_buttons(W, H)
lb_btns      = build_leaderboard_buttons(W, H)
set_btns     = build_settings_buttons(W, H, settings)
saved_score  = None   # kept for game-over display after save


# ── Main loop ─────────────────────────────────────────────────────────────────
while True:
    dt_ms = clock.tick(FPS)
    dt_s  = dt_ms / 1000.0
    keys  = pygame.key.get_pressed()

    # ── Event handling ────────────────────────────────────────────────────────
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()

        # Restore speed after oil/speedbump slow-down
        if event.type == pygame.USEREVENT + 1 and game:
            game["player"].speed = game["player"].BASE_SPEED
            pygame.time.set_timer(pygame.USEREVENT + 1, 0)

        # ── NAME ENTRY ────────────────────────────────────────────────────────
        if STATE == "name_entry":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and name.strip():
                    STATE = "main_menu"
                elif event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                elif event.unicode.isprintable() and len(name) < 16:
                    name += event.unicode

        # ── MAIN MENU ─────────────────────────────────────────────────────────
        elif STATE == "main_menu":
            if menu_btns["play"].is_clicked(event):
                game    = new_game(settings)
                STATE   = "playing"
            elif menu_btns["leaderboard"].is_clicked(event):
                STATE   = "leaderboard"
            elif menu_btns["settings"].is_clicked(event):
                set_btns = build_settings_buttons(W, H, settings)
                STATE    = "settings"
            elif menu_btns["quit"].is_clicked(event):
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()

        # ── SETTINGS ─────────────────────────────────────────────────────────
        elif STATE == "settings":
            if set_btns["sound"].is_clicked(event):
                settings["sound"] = not settings["sound"]
                save_settings(settings)
                set_btns = build_settings_buttons(W, H, settings)
            elif set_btns["car_color"].is_clicked(event):
                colors = ["blue", "red", "green", "yellow"]
                idx    = colors.index(settings["car_color"])
                settings["car_color"] = colors[(idx + 1) % len(colors)]
                save_settings(settings)
                set_btns = build_settings_buttons(W, H, settings)
            elif set_btns["difficulty"].is_clicked(event):
                diffs = ["easy", "normal", "hard"]
                idx   = diffs.index(settings["difficulty"])
                settings["difficulty"] = diffs[(idx + 1) % len(diffs)]
                save_settings(settings)
                set_btns = build_settings_buttons(W, H, settings)
            elif set_btns["back"].is_clicked(event):
                STATE = "main_menu"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                STATE = "main_menu"

        # ── LEADERBOARD ───────────────────────────────────────────────────────
        elif STATE == "leaderboard":
            if lb_btns["back"].is_clicked(event):
                STATE = "main_menu"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                STATE = "main_menu"

        # ── GAME OVER ─────────────────────────────────────────────────────────
        elif STATE == "game_over":
            if go_btns["retry"].is_clicked(event):
                game  = new_game(settings)
                STATE = "playing"
            elif go_btns["menu"].is_clicked(event):
                menu_btns = build_main_menu_buttons(W, H)
                STATE     = "main_menu"
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                STATE = "main_menu"

    # ── Per-state update & draw ───────────────────────────────────────────────

    if STATE == "name_entry":
        screen.fill((10, 10, 20))
        screen.blit(racer.STREET_IMG, (0, 0))
        draw_name_entry(screen, name, W, H)

    elif STATE == "main_menu":
        draw_main_menu(screen, menu_btns, racer.STREET_IMG, W, H)

    elif STATE == "settings":
        screen.fill((10, 10, 20))
        screen.blit(racer.STREET_IMG, (0, 0))
        draw_settings(screen, set_btns, W, H)

    elif STATE == "leaderboard":
        screen.fill((10, 10, 20))
        draw_leaderboard(screen, lb_btns, W, H)

    elif STATE == "playing":
        dead = update_game(game, keys, dt_s)
        draw_game(game)
        if dead:
            # Save to leaderboard
            save_score(name.strip() or "ACE",
                       game["score"],
                       int(game["distance"]),
                       game["player"].coins)
            go_btns = build_gameover_buttons(W, H)
            STATE   = "game_over"

    elif STATE == "game_over":
        # Keep drawing the last game frame underneath the overlay
        draw_game(game)
        draw_game_over(screen, go_btns,
                       game["score"],
                       int(game["distance"]),
                       game["player"].coins,
                       W, H)

    pygame.display.flip()
