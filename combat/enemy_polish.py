"""
Enemy and boss visual polish.
Adds telegraphing, readability, and visual feedback for enemies.
"""

import pygame
import math
from typing import Optional


class EnemyTelegraph:
    """Visual telegraphing for incoming attacks."""
    
    def __init__(self, x: float, y: float, attack_type: str = "melee",
                duration: float = 0.5):
        self.x = x
        self.y = y
        self.attack_type = attack_type
        self.duration = duration
        self.elapsed = 0.0
        self.active = True
    
    def update(self, dt: float) -> bool:
        """Update telegraph. Return True if still active."""
        self.elapsed += dt
        self.active = self.elapsed < self.duration
        return self.active
    
    def render(self, surface: pygame.Surface, offset_x: float, offset_y: float) -> None:
        """Render attack telegraph."""
        if not self.active:
            return
        
        screen_x = int(self.x - offset_x)
        screen_y = int(self.y - offset_y)
        
        progress = self.elapsed / self.duration
        
        if self.attack_type == "melee":
            # Melee telegraph: expanding red circle
            radius = int(50 * progress)
            alpha = int(200 * (1.0 - progress))
            
            telegraph_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(telegraph_surface, (255, 0, 0, alpha), (radius, radius), radius)
            surface.blit(telegraph_surface, (screen_x - radius, screen_y - radius))
        
        elif self.attack_type == "projectile":
            # Projectile telegraph: charging effect
            size = int(30 + 20 * progress)
            pygame.draw.circle(surface, (255, 100, 0), (screen_x, screen_y), size, 2)
        
        elif self.attack_type == "aoe":
            # Area telegraph: expanding zone
            radius = int(100 * progress)
            alpha = int(100 * (1.0 - progress))
            
            telegraph_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(telegraph_surface, (255, 50, 50, alpha), (radius, radius), radius)
            surface.blit(telegraph_surface, (screen_x - radius, screen_y - radius))


class EnemyHealthBar:
    """Visual health bar for enemies."""
    
    def __init__(self, max_width: int = 100, height: int = 8):
        self.max_width = max_width
        self.height = height
        self.offset_y = -30  # Above entity
    
    def render(self, surface: pygame.Surface, x: float, y: float, health: float,
              max_health: float, offset_x: float, offset_y: float) -> None:
        """Render health bar."""
        if max_health <= 0:
            return
        
        screen_x = int(x - offset_x)
        screen_y = int(y - offset_y + self.offset_y)
        
        # Health ratio
        ratio = health / max_health
        
        # Background
        bg_rect = pygame.Rect(screen_x - self.max_width // 2, screen_y,
                             self.max_width, self.height)
        pygame.draw.rect(surface, (50, 50, 50), bg_rect)
        pygame.draw.rect(surface, (100, 100, 100), bg_rect, 1)
        
        # Health bar
        bar_width = int(self.max_width * ratio)
        bar_rect = pygame.Rect(screen_x - self.max_width // 2, screen_y,
                              bar_width, self.height)
        
        # Color based on health
        if ratio > 0.5:
            color = (0, 255, 0)
        elif ratio > 0.25:
            color = (255, 200, 0)
        else:
            color = (255, 0, 0)
        
        pygame.draw.rect(surface, color, bar_rect)


class BossHealthBar:
    """Large health bar for bosses."""
    
    def __init__(self, screen_width: int = 1280, screen_height: int = 720):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.bar_width = 400
        self.bar_height = 30
        self.x = screen_width // 2
        self.y = 100
    
    def render(self, surface: pygame.Surface, health: float, max_health: float,
              boss_name: str = "Boss") -> None:
        """Render boss health bar."""
        if max_health <= 0:
            return
        
        ratio = health / max_health
        
        # Title
        font = pygame.font.SysFont(None, 28)
        title_surface = font.render(boss_name, True, (200, 100, 0))
        surface.blit(title_surface, (self.x - title_surface.get_width() // 2, self.y - 40))
        
        # Background
        bg_rect = pygame.Rect(self.x - self.bar_width // 2, self.y,
                             self.bar_width, self.bar_height)
        pygame.draw.rect(surface, (50, 50, 50), bg_rect)
        pygame.draw.rect(surface, (200, 100, 0), bg_rect, 3)
        
        # Health bar
        bar_width = int(self.bar_width * ratio)
        bar_rect = pygame.Rect(self.x - self.bar_width // 2, self.y,
                              bar_width, self.bar_height)
        pygame.draw.rect(surface, (200, 0, 0), bar_rect)
        
        # Health text
        health_font = pygame.font.SysFont(None, 20)
        health_text = health_font.render(f"{int(health)}/{int(max_health)}", True, (255, 255, 255))
        surface.blit(health_text, (self.x - health_text.get_width() // 2,
                                  self.y + self.bar_height // 2 - health_text.get_height() // 2))


class BossIntroSequence:
    """Boss introduction/spawn animation."""
    
    def __init__(self, duration: float = 2.0):
        self.duration = duration
        self.elapsed = 0.0
        self.active = True
        self.scale = 0.0
        self.alpha = 0
    
    def update(self, dt: float) -> bool:
        """Update intro. Return True if complete."""
        self.elapsed += dt
        
        progress = min(1.0, self.elapsed / self.duration)
        
        # Scale in
        self.scale = progress
        self.alpha = int(255 * progress)
        
        self.active = self.elapsed < self.duration
        return not self.active
    
    def render(self, surface: pygame.Surface, x: float, y: float,
              offset_x: float, offset_y: float, base_surface: pygame.Surface) -> None:
        """Render boss intro."""
        if not self.active or self.scale <= 0:
            return
        
        screen_x = int(x - offset_x)
        screen_y = int(y - offset_y)
        
        # Scale and fade boss sprite
        if self.scale != 1.0:
            new_size = (int(base_surface.get_width() * self.scale),
                       int(base_surface.get_height() * self.scale))
            scaled = pygame.transform.scale(base_surface, new_size)
            scaled.set_alpha(self.alpha)
            surface.blit(scaled, (screen_x - new_size[0] // 2, screen_y - new_size[1] // 2))
        else:
            base_surface.set_alpha(self.alpha)
            surface.blit(base_surface, (screen_x - base_surface.get_width() // 2,
                                       screen_y - base_surface.get_height() // 2))
            base_surface.set_alpha(255)
        
        # Draw circular glow
        glow_radius = int(100 * self.scale)
        glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, (200, 100, 50, int(100 * (1.0 - self.scale))),
                         (glow_radius, glow_radius), glow_radius)
        surface.blit(glow_surface, (screen_x - glow_radius, screen_y - glow_radius))


class BossDeathSequence:
    """Boss death/defeat animation."""
    
    def __init__(self, duration: float = 2.0):
        self.duration = duration
        self.elapsed = 0.0
        self.active = True
        self.scale = 1.0
        self.rotation = 0.0
        self.alpha = 255
    
    def update(self, dt: float) -> bool:
        """Update death animation."""
        self.elapsed += dt
        
        progress = self.elapsed / self.duration
        
        # Spin and shrink
        self.rotation = progress * 360
        self.scale = 1.0 - progress * 0.8
        self.alpha = int(255 * (1.0 - progress))
        
        self.active = self.elapsed < self.duration
        return not self.active
    
    def render(self, surface: pygame.Surface, x: float, y: float,
              offset_x: float, offset_y: float, base_surface: pygame.Surface) -> None:
        """Render boss death."""
        if not self.active or self.scale <= 0:
            return
        
        screen_x = int(x - offset_x)
        screen_y = int(y - offset_y)
        
        # Rotate and scale
        rotated = pygame.transform.rotate(base_surface, self.rotation)
        if self.scale != 1.0:
            new_size = (int(rotated.get_width() * self.scale),
                       int(rotated.get_height() * self.scale))
            rotated = pygame.transform.scale(rotated, new_size)
        
        rotated.set_alpha(self.alpha)
        surface.blit(rotated, (screen_x - rotated.get_width() // 2,
                              screen_y - rotated.get_height() // 2))
