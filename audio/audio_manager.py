"""
Audio management system.
Handles music, SFX, and ambient sounds.
"""

import pygame
import os
from typing import Dict, Optional


class AudioManager:
    """Manages all game audio."""
    
    def __init__(self):
        pygame.mixer.init()
        
        self.music_dir = "assets/sounds/music"
        self.sfx_dir = "assets/sounds/sfx"
        self.ambient_dir = "assets/sounds/ambient"
        self.ui_dir = "assets/sounds/ui"
        
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.music_volume: float = 0.7
        self.sfx_volume: float = 0.8
        self.ambient_volume: float = 0.5
        
        self.current_music: Optional[str] = None
        self.music_fading: bool = False
        self.music_fade_speed: float = 1.0
    
    def load_sound(self, path: str, category: str = "sfx") -> Optional[pygame.mixer.Sound]:
        """Load a sound file."""
        if path in self.sounds:
            return self.sounds[path]
        
        # Build full path based on category
        if category == "music":
            full_path = os.path.join(self.music_dir, path)
        elif category == "ambient":
            full_path = os.path.join(self.ambient_dir, path)
        elif category == "ui":
            full_path = os.path.join(self.ui_dir, path)
        else:
            full_path = os.path.join(self.sfx_dir, path)
        
        # Try to load
        if not os.path.exists(full_path):
            print(f"Audio file not found: {full_path}")
            return None
        
        try:
            sound = pygame.mixer.Sound(full_path)
            self.sounds[path] = sound
            return sound
        except Exception as e:
            print(f"Failed to load audio {full_path}: {e}")
            return None
    
    def play_sfx(self, sound_name: str, volume: float = 1.0) -> None:
        """Play a sound effect."""
        sound = self.load_sound(sound_name, "sfx")
        if sound:
            sound.set_volume(self.sfx_volume * volume)
            sound.play()
    
    def play_ui_sound(self, sound_name: str, volume: float = 1.0) -> None:
        """Play a UI sound."""
        sound = self.load_sound(sound_name, "ui")
        if sound:
            sound.set_volume(self.sfx_volume * volume)
            sound.play()
    
    def play_ambient(self, sound_name: str, volume: float = 1.0, loops: int = -1) -> None:
        """Play ambient sound (looping)."""
        sound = self.load_sound(sound_name, "ambient")
        if sound:
            sound.set_volume(self.ambient_volume * volume)
            sound.play(loops)
    
    def play_music(self, music_name: str, fade_in: float = 0.0) -> None:
        """Play background music."""
        music_path = os.path.join(self.music_dir, music_name)
        
        if not os.path.exists(music_path):
            print(f"Music file not found: {music_path}")
            return
        
        try:
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(self.music_volume)
            
            if fade_in > 0:
                pygame.mixer.music.play(-1)  # -1 = infinite loop
            else:
                pygame.mixer.music.play(-1)
            
            self.current_music = music_name
        except Exception as e:
            print(f"Failed to play music {music_path}: {e}")
    
    def stop_music(self, fade_out: float = 0.0) -> None:
        """Stop background music."""
        if fade_out > 0:
            pygame.mixer.music.fadeout(int(fade_out * 1000))
        else:
            pygame.mixer.music.stop()
        self.current_music = None
    
    def set_music_volume(self, volume: float) -> None:
        """Set music volume (0.0 to 1.0)."""
        self.music_volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.music_volume)
    
    def set_sfx_volume(self, volume: float) -> None:
        """Set SFX volume (0.0 to 1.0)."""
        self.sfx_volume = max(0.0, min(1.0, volume))
    
    def set_ambient_volume(self, volume: float) -> None:
        """Set ambient volume (0.0 to 1.0)."""
        self.ambient_volume = max(0.0, min(1.0, volume))
    
    def stop_all_sounds(self) -> None:
        """Stop all active sounds."""
        pygame.mixer.stop()
        self.stop_music()
    
    def clear_cache(self) -> None:
        """Clear cached sounds to free memory."""
        self.sounds.clear()


# Combat sounds
class CombatSoundManager:
    """Manages combat-related audio."""
    
    def __init__(self, audio_manager: AudioManager):
        self.audio = audio_manager
    
    def play_attack_sound(self, attack_type: str = "melee") -> None:
        """Play attack sound."""
        sounds = {
            "melee": "attack_melee.wav",
            "heavy": "attack_heavy.wav",
            "projectile": "attack_projectile.wav",
        }
        self.audio.play_sfx(sounds.get(attack_type, "attack_melee.wav"))
    
    def play_hit_sound(self, hit_type: str = "normal") -> None:
        """Play hit sound."""
        sounds = {
            "normal": "hit_normal.wav",
            "heavy": "hit_heavy.wav",
            "critical": "hit_critical.wav",
            "block": "hit_block.wav",
        }
        self.audio.play_sfx(sounds.get(hit_type, "hit_normal.wav"))
    
    def play_damage_sound(self) -> None:
        """Play player damage sound."""
        self.audio.play_sfx("damage_taken.wav")
    
    def play_death_sound(self, entity_type: str = "player") -> None:
        """Play death sound."""
        sounds = {
            "player": "death_player.wav",
            "enemy": "death_enemy.wav",
            "boss": "death_boss.wav",
        }
        self.audio.play_sfx(sounds.get(entity_type, "death_enemy.wav"))
    
    def play_boss_sound(self, event: str = "spawn") -> None:
        """Play boss-related sound."""
        sounds = {
            "spawn": "boss_spawn.wav",
            "attack": "boss_attack.wav",
            "phase": "boss_phase.wav",
        }
        self.audio.play_sfx(sounds.get(event, "boss_spawn.wav"))


# Global audio manager
_audio_manager: Optional[AudioManager] = None

def get_audio_manager() -> AudioManager:
    """Get or create global audio manager."""
    global _audio_manager
    if _audio_manager is None:
        _audio_manager = AudioManager()
    return _audio_manager
