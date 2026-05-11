"""
Boss Manager
Handles boss spawning, phase transitions, and arena locks
"""
from typing import Dict, List, Optional, Tuple
import pygame
from entities.boss import Boss
from settings import *


class BossManager:
    """
    Manages boss encounters and arena states
    """
    def __init__(self, world_manager, player):
        self.world_manager = world_manager
        self.player = player
        self.active_boss: Optional[Boss] = None
        self.arena_locked = False
        self.arena_bounds: Optional[pygame.Rect] = None
        self.boss_intro_timer = 0.0
        self.boss_intro_active = False
        self.boss_music_playing = False
        
    def spawn_boss(self, boss_type: str, x: float, y: float):
        """Spawn a boss and lock the arena"""
        # Instantiate specific boss class based on boss_type
        if boss_type == "mecha_beast":
            from entities.boss_mecha import MechaBeast
            self.active_boss = MechaBeast(x, y)
        elif boss_type == "crystal_titan":
            from entities.boss_crystal import CrystalTitan
            self.active_boss = CrystalTitan(x, y)
        elif boss_type == "toxic_worm":
            from entities.boss_toxic import ToxicWorm
            self.active_boss = ToxicWorm(x, y)
        elif boss_type == "void_guardian":
            from entities.boss_void import VoidGuardian
            self.active_boss = VoidGuardian(x, y)
        else:
            self.active_boss = Boss(x, y, name=boss_type)
            self.active_boss.boss_type = boss_type
        
        # Lock arena
        from world.boss_arena import BossArena
        self.arena = BossArena(x - 1000, y - 1000, 2000, 2000, "world")
        self.arena.activate()
        self.arena_locked = True
        
        # Trigger intro
        self.boss_intro_active = True
        self.boss_intro_timer = 3.0
        self.boss_music_playing = True
        
    def update(self, dt: float) -> None:
        """Update boss state and arena"""
        if self.boss_intro_active:
            self.boss_intro_timer -= dt
            if self.boss_intro_timer <= 0:
                self.boss_intro_active = False
        
        if self.active_boss:
            if self.active_boss.is_dead:
                self.arena_locked = False
                if hasattr(self, 'arena'):
                    self.arena.deactivate()
                self.active_boss = None
                self.boss_music_playing = False
    
    def is_in_arena(self, x: float, y: float) -> bool:
        """Check if position is within the locked arena"""
        if not hasattr(self, 'arena') or not self.arena.is_active:
            return False
        return self.arena.rect.collidepoint(x, y)
    
    def get_boss_health_info(self) -> Tuple[float, float, str]:
        """Get health for UI bar"""
        if not self.active_boss:
            return 0, 0, ""
        return self.active_boss.health, self.active_boss.max_health, getattr(self.active_boss, 'name', 'BOSS')
