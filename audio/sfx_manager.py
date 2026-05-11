"""
SFX manager for Void Frontier.
Handles sound effects playback with pooling and spatial foundation.
"""

import pygame
import os
from typing import Dict, Optional

class SFXManager:
    """
    Manages sound effects playback and caching.
    """
    
    def __init__(self, sfx_dir: str = "assets/sounds/sfx"):
        self.sfx_dir = sfx_dir
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.volume: float = 0.7
        
    def load_sound(self, filename: str) -> Optional[pygame.mixer.Sound]:
        """Load and cache a sound effect."""
        if filename in self.sounds:
            return self.sounds[filename]
            
        full_path = os.path.join(self.sfx_dir, filename)
        if not os.path.exists(full_path):
            # Try other subdirs if not in root sfx
            for subdir in ["ui", "combat", "world"]:
                alt_path = os.path.join(self.sfx_dir, "..", subdir, filename)
                if os.path.exists(alt_path):
                    full_path = alt_path
                    break
        
        if not os.path.exists(full_path):
            return None
            
        try:
            sound = pygame.mixer.Sound(full_path)
            sound.set_volume(self.volume)
            self.sounds[filename] = sound
            return sound
        except Exception as e:
            print(f"Failed to load SFX {full_path}: {e}")
            return None
            
    def play(self, filename: str, volume: Optional[float] = None, loops: int = 0):
        """Play a sound effect."""
        sound = self.load_sound(filename)
        if sound:
            channel = sound.play(loops=loops)
            if channel and volume is not None:
                channel.set_volume(volume)
            elif channel:
                channel.set_volume(self.volume)
            return channel
        return None
        
    def set_volume(self, volume: float):
        """Set global SFX volume."""
        self.volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            sound.set_volume(self.volume)
            
    def stop_all(self):
        """Stop all currently playing sound effects."""
        pygame.mixer.stop()
