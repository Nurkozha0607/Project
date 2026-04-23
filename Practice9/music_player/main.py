"""
Music Player - Main Entry Point
================================
Run this file to start the player.
Place your MP3/WAV files inside the  music/  folder first.
"""

import pygame
import sys
import os
from player import MusicPlayer


WINDOW_WIDTH = 700
WINDOW_HEIGHT = 480
FPS = 60


BG_COLOR = (18, 18, 28)
PANEL_COLOR = (28, 28, 42)
ACCENT_COLOR = (100, 80, 220)
ACCENT_LIGHT = (140, 120, 255)
TEXT_PRIMARY = (240, 240, 255)
TEXT_SECONDARY = (150, 150, 180)
TEXT_MUTED = ( 90, 90, 120)
BAR_BG_COLOR = ( 45, 45, 65)
BAR_FG_COLOR = (100, 80, 220)
BAR_DONE_COLOR = (70, 60, 160)
HOTKEY_BG = ( 38, 38, 58)
GREEN_COLOR = (80, 200, 120)
RED_COLOR = (220, 80, 80)


def draw_text(surface, text, font, color, x, y, align="left"):
    """Render text with optional alignment anchor."""
    img = font.render(text, True, color)
    if align == "center":
        x -= img.get_width() // 2
    elif align == "right":
        x -= img.get_width()
    surface.blit(img, (x, y))
    return img.get_width()


def draw_rounded_rect(surface, color, rect, radius=12, border=0, border_color=None):
    """Draw a filled rounded rectangle, with optional border."""
    pygame.draw.rect(surface, color, rect, border_radius=radius)
    if border and border_color:
        pygame.draw.rect(surface, border_color, rect, border, border_radius=radius)


def draw_progress_bar(surface, x, y, width, height, progress, bg, fg, radius=6):
    """Draw a progress bar (progress in 0.0-1.0)."""
    draw_rounded_rect(surface, bg, (x, y, width, height), radius)
    if progress > 0:
        fill_w = max(radius * 2, int(width * min(progress, 1.0)))
        draw_rounded_rect(surface, fg, (x, y, fill_w, height), radius)


def format_time(seconds):
    """Format seconds → MM:SS string."""
    seconds = max(0, int(seconds))
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def main():
    pygame.init()
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("🎵 Music Player")
    clock = pygame.time.Clock()

    # Fonts 
    font_title  = pygame.font.SysFont("Segoe UI", 26, bold=True)
    font_artist = pygame.font.SysFont("Segoe UI", 18)
    font_body   = pygame.font.SysFont("Segoe UI", 15)
    font_small  = pygame.font.SysFont("Segoe UI", 13)
    font_mono   = pygame.font.SysFont("Courier New", 13)

    # Music player
    music_dir = os.path.join(os.path.dirname(__file__), "music")
    player = MusicPlayer(music_dir)

    HOTKEYS = [
        ("P", "Play / Pause"),
        ("S", "Stop"),
        ("N", "Next track"),
        ("B", "Back"),
        ("Q", "Quit"),
    ]

    running = True
    while running:
        # Events 
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                key = pygame.key.name(event.key).upper()

                if key == "P":
                    player.toggle_play()
                elif key == "S":
                    player.stop()
                elif key == "N":
                    player.next_track()
                elif key == "B":
                    player.prev_track()
                elif key == "Q":
                    running = False

            # Progress-bar click-to-seek
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                bar_x, bar_y = 60, 300
                bar_w = WINDOW_WIDTH - 120
                if bar_y <= my <= bar_y + 14 and bar_x <= mx <= bar_x + bar_w:
                    ratio = (mx - bar_x) / bar_w
                    player.seek(ratio)

        player.update()

        # Draw 
        screen.fill(BG_COLOR)

        # Header panel
        draw_rounded_rect(screen, PANEL_COLOR, (20, 20, WINDOW_WIDTH - 40, 80), radius=14)

        # App title
        draw_text(screen, "♫  Music Player", font_artist, ACCENT_LIGHT, 44, 38)

        # Status indicator
        status_color = GREEN_COLOR if player.is_playing() else (
            TEXT_MUTED if player.state == "stopped" else ACCENT_COLOR
        )
        status_label = (
            "▶  Playing" if player.is_playing() else
            "⏸  Paused"  if player.state == "paused" else
            "■  Stopped"
        )
        draw_text(screen, status_label, font_body, status_color,
                  WINDOW_WIDTH - 44, 46, align="right")

        # Playlist count
        count_txt = f"{len(player.playlist)} track{'s' if len(player.playlist) != 1 else ''} in library"
        draw_text(screen, count_txt, font_small, TEXT_MUTED, 44, 66)

        # ── Track info panel 
        draw_rounded_rect(screen, PANEL_COLOR, (20, 118, WINDOW_WIDTH - 40, 130), radius=14)

        if player.playlist:
            idx  = player.current_index
            name = player.get_track_name()

            # Index badge
            badge_txt = f"{idx + 1} / {len(player.playlist)}"
            draw_rounded_rect(screen, HOTKEY_BG, (44, 134, 66, 24), radius=8)
            draw_text(screen, badge_txt, font_small, ACCENT_LIGHT, 77, 139, align="center")

            # Track name (truncate if needed)
            max_chars = 46
            display_name = name if len(name) <= max_chars else name[:max_chars - 1] + "…"
            draw_text(screen, display_name, font_title, TEXT_PRIMARY, 124, 130)

            # Filename
            fname = os.path.basename(player.playlist[idx])
            fname_display = fname if len(fname) <= 55 else fname[:54] + "…"
            draw_text(screen, fname_display, font_small, TEXT_MUTED, 124, 162)

            # Playlist preview 
            prev_tracks = player.get_surrounding_tracks(before=1, after=2)
            y_pl = 192
            for track_idx, track_name in prev_tracks:
                is_current = (track_idx == idx)
                color = ACCENT_LIGHT if is_current else TEXT_MUTED
                prefix = "▶ " if is_current else f"  {track_idx + 1}. "
                draw_text(screen, prefix + track_name, font_small, color, 124, y_pl)
                y_pl += 17

        else:
            draw_text(screen, "No tracks found", font_title, TEXT_MUTED,
                      WINDOW_WIDTH // 2, 168, align="center")
            draw_text(screen, f"Add MP3/WAV files to:  {music_dir}",
                      font_small, TEXT_MUTED, WINDOW_WIDTH // 2, 195, align="center")

        # Progress bar
        bar_x, bar_y = 60, 300
        bar_w = WINDOW_WIDTH - 120

        elapsed  = player.get_position()
        duration = player.get_duration()
        progress = (elapsed / duration) if duration > 0 else 0.0

        draw_progress_bar(screen, bar_x, bar_y, bar_w, 14,
                          progress, BAR_BG_COLOR, BAR_FG_COLOR)

        # Seek handle
        if duration > 0:
            hx = bar_x + int(bar_w * min(progress, 1.0))
            pygame.draw.circle(screen, ACCENT_LIGHT, (hx, bar_y + 7), 8)
            pygame.draw.circle(screen, BG_COLOR,     (hx, bar_y + 7), 4)

        # Time stamps
        draw_text(screen, format_time(elapsed),  font_mono, TEXT_SECONDARY, bar_x,          bar_y + 22)
        draw_text(screen, format_time(duration), font_mono, TEXT_SECONDARY, bar_x + bar_w,  bar_y + 22, align="right")

        # Hotkeys panel
        draw_rounded_rect(screen, PANEL_COLOR, (20, 360, WINDOW_WIDTH - 40, 100), radius=14)

        kx = 44
        for key, label in HOTKEYS:
            # Key badge
            draw_rounded_rect(screen, HOTKEY_BG, (kx, 378, 26, 22), radius=6,
                               border=1, border_color=ACCENT_COLOR)
            draw_text(screen, key, font_small, ACCENT_LIGHT, kx + 13, 383, align="center")
            # Label
            draw_text(screen, label, font_small, TEXT_SECONDARY, kx + 32, 383)
            kx += 108

        draw_text(screen, "Click the progress bar to seek",
                  font_small, TEXT_MUTED, WINDOW_WIDTH // 2, 418, align="center")

        pygame.display.flip()
        clock.tick(FPS)

    player.stop()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()