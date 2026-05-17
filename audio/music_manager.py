"""
Music manager for Void Frontier.
Handles background music, transitions, and biome-specific tracks.
"""

import pygame
import os
from typing import Optional, Dict

class MusicManager:
    """
    Manages background music playback and transitions.
    """
    
    def __init__(self, music_dir: str = "assets/sounds/music"):
        self.music_dir = music_dir
        self.current_track: Optional[str] = None
        self.volume: float = 0.5
        
        # Biome to music mapping (matches actual filenames on disk)
        self.biome_tracks = {
            "toxic_plains": "toxic ambience.mp3",
            "crystal_desert": "crystal cave ambience.mp3",
            "fungal_cave": "fungal ambience.mp3",
            "void_ruins": "void ambient.mp3",
            "boss_fight": "boss battle music.mp3",
            "menu": "game menu theme.mp3"
        }
        
    def play_track(self, track_name: str, loop: int = -1, fade_ms: int = 2000):
        """Play a music track by filename or biome key."""
        # Check if it's a biome key
        filename = self.biome_tracks.get(track_name, track_name)
        full_path = os.path.join(self.music_dir, filename)
        
        if not os.path.exists(full_path):
            print(f"Music track not found: {full_path}")
            return
            
        if self.current_track == full_path:
            return
            
        try:
            pygame.mixer.music.load(full_path)
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play(loop, fade_ms=fade_ms)
            self.current_track = full_path
        except Exception as e:
            print(f"Failed to play music {full_path}: {e}")
            
    def stop(self, fade_ms: int = 1000):
        """Stop music with fade out."""
        pygame.mixer.music.fadeout(fade_ms)
        self.current_track = None
        
    def set_volume(self, volume: float):
        """Set music volume (0.0 to 1.0)."""
        self.volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.volume)
        
    def pause(self):
        """Pause music."""
        pygame.mixer.music.pause()
        
    def resume(self):
        """Resume music."""
        pygame.mixer.music.unpause()
