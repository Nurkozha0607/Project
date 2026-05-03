# ──────────────────────────────────────────────────────────────────────────────
# persistence.py
# Responsible for: all file I/O — reading and writing leaderboard.json and
# settings.json so scores and preferences survive between sessions.
# ──────────────────────────────────────────────────────────────────────────────

import json
import os

# Paths sit next to this file (inside the TSIS3 folder)
BASE_DIR         = os.path.dirname(os.path.abspath(__file__))
LEADERBOARD_FILE = os.path.join(BASE_DIR, "leaderboard.json")
SETTINGS_FILE    = os.path.join(BASE_DIR, "settings.json")

# ── Default values ────────────────────────────────────────────────────────────
DEFAULT_SETTINGS = {
    "sound":      True,
    "car_color":  "blue",      # "blue" | "red" | "green" | "yellow"
    "difficulty": "normal",    # "easy" | "normal" | "hard"
}


# ── Settings ──────────────────────────────────────────────────────────────────

def load_settings() -> dict:
    """Return saved settings, or defaults if the file does not exist."""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
            # Fill in any missing keys with defaults
            for key, val in DEFAULT_SETTINGS.items():
                data.setdefault(key, val)
            return data
        except (json.JSONDecodeError, IOError):
            pass
    return dict(DEFAULT_SETTINGS)


def save_settings(settings: dict) -> None:
    """Write settings dict to settings.json."""
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)


# ── Leaderboard ───────────────────────────────────────────────────────────────

def load_leaderboard() -> list:
    """
    Return list of score entries (up to 10), each entry is a dict:
      { "name": str, "score": int, "distance": int, "coins": int }
    Sorted descending by score.
    """
    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE, "r") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
        except (json.JSONDecodeError, IOError):
            pass
    return []


def save_score(name: str, score: int, distance: int, coins: int) -> list:
    """
    Append a new score entry, keep only top 10 by score, write to disk.
    Returns the updated leaderboard list.
    """
    board = load_leaderboard()
    board.append({
        "name":     name,
        "score":    score,
        "distance": distance,
        "coins":    coins,
    })
    # Sort descending, keep top 10
    board.sort(key=lambda e: e["score"], reverse=True)
    board = board[:10]
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(board, f, indent=2)
    return board
