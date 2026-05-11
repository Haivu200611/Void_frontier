"""
Visual effects system for glow, distortion, and other screen effects.
"""

import pygame
import math
from typing import Tuple, Optional


class GlowEffect:
    """Glow effect for entities."""
    
    def __init__(self, x: float, y: float, size: float, color: Tuple[int, int, int],
                 intensity: float = 1.0, pulse_speed: float = 1.0):
        self.x = x
        self.y = y
        self.size = size
        self.color = color
        self.intensity = intensity
        self.pulse_speed = pulse_speed
        self.time = 0.0
    
    def update(self, dt: float) -> None:
        """Update glow animation."""
        self.time += dt
    
    def render(self, surface: pygame.Surface, offset_x: float, offset_y: float) -> None:
        """Render glow."""
        # Pulsing glow effect
        pulse = math.sin(self.time * self.pulse_speed * 2 * math.pi) * 0.5 + 0.5
        size = self.size * (0.8 + pulse * 0.4)
        alpha = int(255 * self.intensity * pulse)
        
        # Create glow surface
        glow_size = int(size * 2)
        glow_surface = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        
        # Draw gradient glow
        center = glow_size // 2
        for r in range(glow_size // 2, 0, -1):
            alpha_val = int(255 * (1.0 - (r / (glow_size // 2))) * self.intensity * pulse)
            pygame.draw.circle(glow_surface, (*self.color, alpha_val), (center, center), r)
        
        # Blit to screen
        screen_x = int(self.x - offset_x)
        screen_y = int(self.y - offset_y)
        surface.blit(glow_surface, (screen_x - center, screen_y - center))


class PortalEffectRenderer:
    """Renders portal visual effects."""
    
    def __init__(self):
        self.time = 0.0
    
    def update(self, dt: float) -> None:
        """Update animation."""
        self.time += dt
    
    def render(self, surface: pygame.Surface, x: float, y: float, offset_x: float,
              offset_y: float, radius: float = 40) -> None:
        """Render portal effect."""
        screen_x = int(x - offset_x)
        screen_y = int(y - offset_y)
        
        # Rotating rings
        rotation = (self.time * 90) % 360
        
        # Draw outer ring
        ring_radius = radius * 1.5
        for i in range(3):
            angle = rotation + i * 120
            rad = math.radians(angle)
            
            p1_x = screen_x + math.cos(rad) * ring_radius
            p1_y = screen_y + math.sin(rad) * ring_radius
            
            p2_x = screen_x + math.cos(rad + math.pi / 3) * ring_radius
            p2_y = screen_y + math.sin(rad + math.pi / 3) * ring_radius
            
            pygame.draw.line(surface, (50, 200, 200), (p1_x, p1_y), (p2_x, p2_y), 3)
        
        # Draw pulsing center
        pulse = math.sin(self.time * 3) * 0.5 + 0.5
        center_radius = radius * (0.5 + pulse * 0.5)
        pygame.draw.circle(surface, (50, 200, 200), (screen_x, screen_y), int(center_radius), 2)


class ToxicFogEffect:
    """Renders toxic fog effect."""
    
    def __init__(self, x: float, y: float, size: float = 100):
        self.x = x
        self.y = y
        self.size = size
        self.time = 0.0
    
    def update(self, dt: float) -> None:
        """Update fog animation."""
        self.time += dt
    
    def render(self, surface: pygame.Surface, offset_x: float, offset_y: float) -> None:
        """Render toxic fog."""
        screen_x = int(self.x - offset_x)
        screen_y = int(self.y - offset_y)
        
        # Pulsing toxic clouds
        wave = math.sin(self.time * 2) * 0.5 + 0.5
        
        # Draw multiple layers
        for layer in range(3):
            layer_offset = layer * 30
            layer_alpha = int(150 * (1.0 - layer * 0.2) * wave)
            
            fog_surface = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
            center = int(self.size)
            pygame.draw.circle(fog_surface, (100, 200, 50, layer_alpha), (center, center),
                             int(self.size - layer_offset))
            
            surface.blit(fog_surface, (screen_x - center, screen_y - center))


class LightingEffect:
    """Simple lighting overlay."""
    
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.light_surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        self.lights = []
    
    def add_light(self, x: float, y: float, radius: float, color: Tuple[int, int, int],
                 intensity: float = 1.0) -> None:
        """Add a light source."""
        self.lights.append({
            'x': x,
            'y': y,
            'radius': radius,
            'color': color,
            'intensity': intensity
        })
    
    def update(self) -> None:
        """Update lighting."""
        # Create dark overlay
        self.light_surface.fill((0, 0, 0, 200))
        
        # Draw light circles (using additive blend)
        for light in self.lights:
            radius = int(light['radius'])
            center_x = int(light['x'])
            center_y = int(light['y'])
            
            if 0 <= center_x < self.screen_width and 0 <= center_y < self.screen_height:
                pygame.draw.circle(self.light_surface, light['color'], (center_x, center_y),
                                 radius)
        
        self.lights.clear()
    
    def render(self, surface: pygame.Surface) -> None:
        """Render lighting."""
        surface.blit(self.light_surface, (0, 0), special_flags=pygame.BLEND_MULT)


class DistortionEffect:
    """Screen distortion effect."""
    
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.time = 0.0
        self.intensity = 0.0
    
    def trigger(self, intensity: float = 1.0, duration: float = 0.5) -> None:
        """Trigger distortion."""
        self.intensity = intensity
        self.time = duration
    
    def update(self, dt: float) -> None:
        """Update distortion."""
        if self.time > 0:
            self.time -= dt
            if self.time < 0:
                self.intensity = 0.0
    
    def apply(self, surface: pygame.Surface) -> pygame.Surface:
        """Apply distortion to surface."""
        if self.intensity <= 0:
            return surface
        
        # Create distorted copy
        distorted = surface.copy()
        
        # Simple wave distortion
        for y in range(0, self.screen_height, 4):
            offset = int(math.sin(y * 0.01 + self.time * 10) * self.intensity * 5)
            pygame.draw.line(distorted, (0, 0, 0), (0, y), (self.screen_width, y))
        
        return distorted


# Global effects manager
class VisualEffectsManager:
    """Manages all visual effects."""
    
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        self.glows = []
        self.portal_effects = []
        self.toxic_fogs = []
        self.lighting = LightingEffect(screen_width, screen_height)
        self.distortion = DistortionEffect(screen_width, screen_height)
    
    def add_glow(self, x: float, y: float, size: float, color: Tuple[int, int, int],
                intensity: float = 1.0) -> None:
        """Add a glow effect."""
        glow = GlowEffect(x, y, size, color, intensity)
        self.glows.append(glow)
    
    def add_portal_effect(self, x: float, y: float, radius: float = 40) -> None:
        """Add a portal effect."""
        # Portal effect is handled by emitting particles from particle system
        pass
    
    def add_toxic_fog(self, x: float, y: float, size: float = 100) -> None:
        """Add toxic fog effect."""
        fog = ToxicFogEffect(x, y, size)
        self.toxic_fogs.append(fog)
    
    def update(self, dt: float) -> None:
        """Update all effects."""
        for glow in self.glows:
            glow.update(dt)
        
        for fog in self.toxic_fogs:
            fog.update(dt)
        
        # Remove old effects
        self.glows = [g for g in self.glows if g.time < 5.0]  # Keep for 5 seconds
        self.toxic_fogs = [f for f in self.toxic_fogs if f.time < 10.0]  # Keep for 10 seconds
        
        self.lighting.update()
        self.distortion.update(dt)
    
    def render(self, surface: pygame.Surface, offset_x: float, offset_y: float) -> None:
        """Render all effects."""
        for glow in self.glows:
            glow.render(surface, offset_x, offset_y)
        
        for fog in self.toxic_fogs:
            fog.render(surface, offset_x, offset_y)
        
        self.lighting.render(surface)
