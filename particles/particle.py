"""
Single particle class for visual effects.
"""

import pygame
from typing import Tuple

class Particle:
    """Single particle in the system."""
    
    def __init__(self):
        self.x: float = 0
        self.y: float = 0
        self.vx: float = 0
        self.vy: float = 0
        self.lifetime: float = 1.0
        self.age: float = 0.0
        self.color: Tuple[int, int, int] = (255, 255, 255)
        self.size: float = 4.0
        self.alpha: float = 255.0
        self.active: bool = False
        
        # Physics
        self.gravity: float = 0.0
        self.drag: float = 0.98
        self.scale_over_time: bool = False
    
    def update(self, dt: float) -> None:
        """Update particle state."""
        if not self.active:
            return
        
        self.age += dt
        
        # Check if dead
        if self.age >= self.lifetime:
            self.active = False
            return
        
        # Apply physics
        self.vy += self.gravity * dt
        self.vx *= self.drag
        self.vy *= self.drag
        
        # Move
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        # Fade out
        progress = self.age / self.lifetime
        self.alpha = 255 * (1.0 - progress)
        
        # Scale over time
        if self.scale_over_time:
            self.size = self.size * (1.0 - progress * 0.5)
    
    def render(self, surface: pygame.Surface, offset_x: float, offset_y: float) -> None:
        """Render particle to screen."""
        if not self.active:
            return
        
        screen_x = int(self.x - offset_x)
        screen_y = int(self.y - offset_y)
        size = max(1, int(self.size))
        
        color_with_alpha = (*self.color, int(self.alpha))
        
        # Create temporary surface for alpha
        particle_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.circle(particle_surface, color_with_alpha, (size, size), size)
        surface.blit(particle_surface, (screen_x - size, screen_y - size))
