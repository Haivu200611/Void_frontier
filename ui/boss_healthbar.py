"""
Animated boss health bar system.
"""

import pygame
import math
from settings import *

class BossHealthBar:
    """
    Renders a large, cinematic health bar for bosses.
    Supports animations and phase transitions.
    """
    
    def __init__(self):
        self.font = pygame.font.SysFont(None, 28)
        self.width = WINDOW_WIDTH * 0.6
        self.height = 24
        self.x = (WINDOW_WIDTH - self.width) // 2
        self.y = 40
        
        self.display_health = 0.0
        self.target_health = 0.0
        self.max_health = 100.0
        self.boss_name = "BOSS"
        self.active = False
        self.alpha = 0
        
    def show(self, name: str, max_hp: float):
        self.boss_name = name
        self.max_health = max_hp
        self.display_health = max_hp
        self.active = True
        
    def hide(self):
        self.active = False
        
    def update(self, dt: float, health: float):
        if not self.active:
            if self.alpha > 0:
                self.alpha = max(0, self.alpha - 500 * dt)
            return
            
        if self.alpha < 255:
            self.alpha = min(255, self.alpha + 500 * dt)
            
        self.target_health = health
        self.display_health += (self.target_health - self.display_health) * 3 * dt
        
    def render(self, surface: pygame.Surface):
        if self.alpha <= 0:
            return
            
        ratio = max(0.0, self.display_health / self.max_health) if self.max_health > 0 else 0.0
        
        # Draw background
        bg_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        s = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        s.fill((20, 10, 10, self.alpha))
        surface.blit(s, (self.x, self.y))
        
        # Draw health
        health_w = int(self.width * ratio)
        if health_w > 0:
            health_surf = pygame.Surface((health_w, self.height), pygame.SRCALPHA)
            # Use a gradient or vibrant color
            color = (200, 40, 40, self.alpha)
            if ratio < 0.2:
                color = (255, 100, 50, self.alpha)
            health_surf.fill(color)
            surface.blit(health_surf, (self.x, self.y))
            
        # Draw border
        pygame.draw.rect(surface, (150, 150, 150, self.alpha), bg_rect, 2)
        
        # Draw name
        name_surf = self.font.render(self.boss_name.upper(), True, (255, 255, 255))
        name_surf.set_alpha(self.alpha)
        surface.blit(name_surf, (self.x, self.y - 25))
        
        # Draw value
        val_text = f"{int(self.display_health)} / {int(self.max_health)}"
        val_surf = self.font.render(val_text, True, (255, 255, 255))
        val_surf.set_alpha(self.alpha)
        surface.blit(val_surf, (self.x + self.width - val_surf.get_width(), self.y - 25))
