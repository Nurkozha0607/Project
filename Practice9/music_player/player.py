"""
player.py — MusicPlayer class
==============================
Handles playlist management, playback state, position tracking,
and seeking.  Keeps all audio logic away from the UI layer.
"""

import os
import time
import pygame

# Supported audio formats 
SUPPORTED_EXTS = {".mp3", ".wav", ".ogg", ".flac"}


class MusicPlayer:
    """
    Wraps pygame.mixer to provide a clean playlist-based music player.

    States
    ------
    stopped  → no track loaded / stopped by user
    playing  → audio is currently playing
    paused   → audio paused mid-track
    """

    def __init__(self, music_dir: str):
        self.music_dir      = music_dir
        self.playlist: list = []
        self.current_index  = 0
        self.state          = "stopped"     # "playing" | "paused" | "stopped"

        # Position tracking (pygame.mixer.music.get_pos resets on pause/seek)
        self._duration        = 0.0          # seconds, estimated from file
        self._play_start_time = 0.0          # wall-clock time when play started
        self._elapsed_before  = 0.0          # accumulated elapsed seconds

        self._load_playlist()

    # Playlist

    def _load_playlist(self):
        """Scan music_dir for supported audio files."""
        self.playlist = []
        os.makedirs(self.music_dir, exist_ok=True)

        if os.path.isdir(self.music_dir):
            for fname in sorted(os.listdir(self.music_dir)):
                ext = os.path.splitext(fname)[1].lower()
                if ext in SUPPORTED_EXTS:
                    self.playlist.append(os.path.join(self.music_dir, fname))

    def get_track_name(self, index: int = None) -> str:
        """Return a human-readable track name (filename without extension)."""
        if index is None:
            index = self.current_index
        if not self.playlist:
            return "No tracks loaded"
        fname = os.path.basename(self.playlist[index])
        return os.path.splitext(fname)[0]

    def get_surrounding_tracks(self, before: int = 1, after: int = 2):
        """
        Return a list of (index, name) tuples for tracks surrounding the
        current one, used to render a mini playlist preview in the UI.
        """
        if not self.playlist:
            return []
        result = []
        for offset in range(-before, after + 1):
            idx = self.current_index + offset
            if 0 <= idx < len(self.playlist):
                result.append((idx, self.get_track_name(idx)))
        return result

    # Playback controls

    def play(self, index: int = None):
        """Load and play a track.  Defaults to current_index."""
        if not self.playlist:
            return

        if index is not None:
            self.current_index = max(0, min(index, len(self.playlist) - 1))

        path = self.playlist[self.current_index]
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            self.state              = "playing"
            self._elapsed_before    = 0.0
            self._play_start_time   = time.time()
            self._duration          = self._estimate_duration(path)
        except pygame.error as exc:
            print(f"[MusicPlayer] Could not load '{path}': {exc}")
            self.state = "stopped"

    def toggle_play(self):
        """Play if stopped/paused; pause if playing."""
        if not self.playlist:
            return

        if self.state == "stopped":
            self.play()
        elif self.state == "playing":
            pygame.mixer.music.pause()
            self._elapsed_before += time.time() - self._play_start_time
            self.state = "paused"
        elif self.state == "paused":
            pygame.mixer.music.unpause()
            self._play_start_time = time.time()
            self.state = "playing"

    def stop(self):
        """Stop playback and reset position."""
        pygame.mixer.music.stop()
        self.state            = "stopped"
        self._elapsed_before  = 0.0
        self._play_start_time = 0.0

    def next_track(self):
        """Advance to the next track (wraps around)."""
        if not self.playlist:
            return
        self.current_index = (self.current_index + 1) % len(self.playlist)
        self.play()

    def prev_track(self):
        """Go to the previous track (wraps around)."""
        if not self.playlist:
            return
        self.current_index = (self.current_index - 1) % len(self.playlist)
        self.play()

    def seek(self, ratio: float):
        """
        Seek to a position in the current track.
        ratio  — float in [0.0, 1.0]
        """
        if not self.playlist or self._duration <= 0:
            return

        target_sec = ratio * self._duration

        # pygame.mixer.music.set_pos() works for OGG and some MP3s.
        # For WAV, we must use a start argument in play().
        was_playing = self.state == "playing"

        try:
            ext = os.path.splitext(self.playlist[self.current_index])[1].lower()
            if ext == ".wav":
                pygame.mixer.music.play(start=target_sec)
            else:
                pygame.mixer.music.play(start=target_sec)

            if not was_playing:
                pygame.mixer.music.pause()
                self.state = "paused"
            else:
                self.state = "playing"

            self._elapsed_before  = target_sec
            self._play_start_time = time.time()
        except pygame.error:
            # Seeking not supported — silently ignore
            pass

    # Status queries 

    def is_playing(self) -> bool:
        return self.state == "playing"

    def get_position(self) -> float:
        """Return elapsed playback time in seconds."""
        if self.state == "playing":
            return self._elapsed_before + (time.time() - self._play_start_time)
        return self._elapsed_before

    def get_duration(self) -> float:
        """Return estimated track duration in seconds."""
        return self._duration

    # Internal helpers 

    def update(self):
        """
        Must be called once per frame.
        Detects natural end-of-track and auto-advances to the next one.
        """
        if self.state == "playing" and not pygame.mixer.music.get_busy():
            # Track finished naturally
            self.next_track()

    @staticmethod
    def _estimate_duration(path: str) -> float:
        """
        Estimate track duration in seconds.

        Tries pygame.mixer.Sound for WAV (accurate).
        Falls back to a heuristic for MP3 (file-size based, ±10 %).
        For a production player, use mutagen for accurate MP3 tags.
        """
        ext = os.path.splitext(path)[1].lower()
        try:
            if ext in (".wav", ".ogg", ".flac"):
                snd = pygame.mixer.Sound(path)
                return snd.get_length()
            else:
                # Rough MP3 estimate: 128 kbps → 16 000 bytes/second
                size = os.path.getsize(path)
                return size / 16_000
        except Exception:
            return 0.0