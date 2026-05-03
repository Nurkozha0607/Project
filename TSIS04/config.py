# config.py — Global constants for the Snake game

# Window
WINDOW_WIDTH  = 800
WINDOW_HEIGHT = 640
TITLE         = "Snake — TSIS 3"
FPS           = 60

# Grid
CELL_SIZE  = 20
COLS       = WINDOW_WIDTH  // CELL_SIZE   # 40
ROWS       = (WINDOW_HEIGHT - 80) // CELL_SIZE  # 28  (top 80 px = HUD)
HUD_HEIGHT = 80

# Speeds  (milliseconds between snake moves)
SPEED_NORMAL = 150
SPEED_BOOST  = 75
SPEED_SLOW   = 280

# Colors (defaults — may be overridden by settings.json)
BLACK       = (0,   0,   0)
WHITE       = (255, 255, 255)
DARK_BG     = (18,  18,  28)
PANEL_BG    = (28,  28,  42)
GREEN       = (60,  220, 100)
DARK_GREEN  = (40,  160,  70)
RED         = (220,  60,  60)
DARK_RED    = (140,  20,  20)
YELLOW      = (240, 200,  40)
CYAN        = (60,  220, 220)
ORANGE      = (240, 140,  40)
PURPLE      = (160,  80, 240)
GRAY        = (100, 100, 120)
LIGHT_GRAY  = (180, 180, 200)
ACCENT      = (80,  200, 255)
GOLD        = (255, 200,  40)

# Food colors
FOOD_NORMAL_COLOR  = GREEN
FOOD_RARE_COLOR    = GOLD
FOOD_POISON_COLOR  = DARK_RED

# Power-up colors
POWERUP_SPEED_COLOR  = ORANGE
POWERUP_SLOW_COLOR   = CYAN
POWERUP_SHIELD_COLOR = PURPLE

# Obstacle color
OBSTACLE_COLOR = GRAY

# HUD
HUD_BG       = PANEL_BG
HUD_TEXT     = LIGHT_GRAY

# Levels
LEVEL_SCORE_THRESHOLD = 50   # score per level-up
OBSTACLES_START_LEVEL = 3
OBSTACLES_PER_LEVEL   = 5    # extra blocks added each level ≥ 3

# Food weights  (normal vs rare)
FOOD_NORMAL_WEIGHT = 7
FOOD_RARE_WEIGHT   = 3
FOOD_DISAPPEAR_SEC = 8       # seconds before food disappears
POISON_CHANCE      = 0.25    # probability a new food spawn is poison

# Power-ups
POWERUP_FIELD_LIFE = 8_000   # ms on field before despawn
POWERUP_DURATION   = 5_000   # ms active duration after collection

# Points
POINTS_NORMAL = 10
POINTS_RARE   = 30

# DB  — edit to match your PostgreSQL setup
DB_HOST     = "localhost"
DB_PORT     = 5432
DB_NAME     = "snake_game"
DB_USER     = "postgres"
DB_PASSWORD = "postgres"