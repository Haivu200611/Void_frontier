"""
Environmental immersion systems.
Handles parallax backgrounds, ambient fog, environmental ambience, etc.
"""

import pygame
import math
import random
from typing import List, Tuple, Optional


class ParallaxLayer:
    """A single parallax background layer."""
    
    def __init__(self, image: pygame.Surface, depth: float = 1.0, tile_width: int = 1280):
        self.image = image
        self.depth = depth  # Closer to 0 = farther away
        self.x = 0
        self.y = 0
        self.tile_width = tile_width
        self.tile_height = image.get_height() if image else 0
    
    def update(self, camera_x: float, camera_y: float) -> None:
        """Update parallax position based on camera."""
        # Parallax scrolling
        self.x = -(camera_x * self.depth) % self.tile_width
        self.y = camera_y * self.depth * 0.3  # Vertical parallax is minimal
    
    def render(self, surface: pygame.Surface, screen_width: int, screen_height: int) -> None:
        """Render parallax layer with tiling."""
        if not self.image:
            return
        
        # Render tiles
        for x_offset in range(-1, 3):
            screen_x = int(self.x + x_offset * self.tile_width)
            screen_y = int(-self.y)
            surface.blit(self.image, (screen_x, screen_y))


class AmbientParticleLayer:
    """Ambient particle effects (dust, floating debris, etc.)."""
    
    def __init__(self, particle_count: int = 20):
        self.particles: List[dict] = []
        
        # Spawn initial particles
        for _ in range(particle_count):
            self.particles.append({
                'x': random.uniform(0, 1280),
                'y': random.uniform(0, 720),
                'vx': random.uniform(-10, 10),
                'vy': random.uniform(-20, -5),
                'size': random.uniform(1, 3),
                'alpha': random.uniform(30, 100),
                'lifetime': random.uniform(3, 10),
                'age': 0
            })
    
    def update(self, dt: float) -> None:
        """Update ambient particles."""
        for particle in self.particles:
            particle['age'] += dt
            particle['x'] += particle['vx'] * dt
            particle['y'] += particle['vy'] * dt
            
            # Wrap around screen
            if particle['x'] < 0:
                particle['x'] = 1280
            elif particle['x'] > 1280:
                particle['x'] = 0
            
            if particle['y'] < 0:
                particle['y'] = 720
                particle['age'] = 0  # Reset
            
            # Update alpha based on lifetime
            progress = particle['age'] / particle['lifetime']
            particle['alpha'] = int(100 * (1.0 - progress))
    
    def render(self, surface: pygame.Surface) -> None:
        """Render ambient particles."""
        for particle in self.particles:
            if particle['alpha'] > 0:
                # Create particle surface with alpha
                p_surface = pygame.Surface((int(particle['size'] * 2), int(particle['size'] * 2)),
                                         pygame.SRCALPHA)
                pygame.draw.circle(p_surface, (100, 100, 120, particle['alpha']),
                                 (int(particle['size']), int(particle['size'])),
                                 int(particle['size']))
                surface.blit(p_surface, (int(particle['x']), int(particle['y'])))


class EnvironmentalFogEffect:
    """Screen-space fog effect."""
    
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.time = 0.0
        self.intensity = 0.3
        self.color = (50, 50, 60)
    
    def update(self, dt: float) -> None:
        """Update fog animation."""
        self.time += dt
    
    def set_intensity(self, intensity: float) -> None:
        """Set fog intensity (0-1)."""
        self.intensity = max(0, min(1, intensity))
    
    def render(self, surface: pygame.Surface) -> None:
        """Render fog overlay."""
        if self.intensity <= 0:
            return
        
        # Create fog effect
        fog_surface = pygame.Surface((self.screen_width, self.screen_height))
        fog_surface.fill(self.color)
        
        # Add animation wave
        wave = math.sin(self.time * 0.5) * 0.1
        alpha = int(255 * (self.intensity + wave))
        fog_surface.set_alpha(max(0, min(255, alpha)))
        
        surface.blit(fog_surface, (0, 0))


class MeteorRain:
    """Animated meteor rain effect."""
    
    def __init__(self, screen_width: int = 1280, screen_height: int = 720):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.meteors: List[dict] = []
        self.active = False
        self.duration = 0
        self.elapsed = 0
    
    def trigger(self, duration: float = 5.0, intensity: float = 1.0) -> None:
        """Trigger meteor rain."""
        self.active = True
        self.duration = duration
        self.elapsed = 0
        
        # Spawn meteors
        count = int(10 * intensity)
        for _ in range(count):
            self.meteors.append({
                'x': random.uniform(0, self.screen_width),
                'y': -50,
                'vx': random.uniform(-100, 100),
                'vy': random.uniform(300, 500),
                'size': random.uniform(3, 8),
                'age': 0
            })
    
    def update(self, dt: float) -> None:
        """Update meteor rain."""
        if not self.active:
            return
        
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.active = False
            self.meteors.clear()
            return
        
        # Update meteors
        for meteor in self.meteors:
            meteor['x'] += meteor['vx'] * dt
            meteor['y'] += meteor['vy'] * dt
            meteor['age'] += dt
        
        # Remove old meteors
        self.meteors = [m for m in self.meteors if m['y'] < self.screen_height + 100]
    
    def render(self, surface: pygame.Surface) -> None:
        """Render meteor rain."""
        for meteor in self.meteors:
            x = int(meteor['x'])
            y = int(meteor['y'])
            size = int(meteor['size'])
            
            # Draw meteor with trail
            trail_color = (200, 150, 100)
            pygame.draw.line(surface, trail_color,
                           (x, y), (x - meteor['vx'] * 0.02, y - meteor['vy'] * 0.02), 2)
            
            # Draw meteor
            pygame.draw.circle(surface, (255, 200, 150), (x, y), size)


class EnvironmentalImmersion:
    """Master environmental immersion controller."""
    
    def __init__(self, screen_width: int = 1280, screen_height: int = 720):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        self.parallax_layers: List[ParallaxLayer] = []
        self.ambient_particles = AmbientParticleLayer(15)
        self.fog_effect = EnvironmentalFogEffect(screen_width, screen_height)
        self.meteor_rain = MeteorRain(screen_width, screen_height)
        
        self.current_biome = "toxic_plains"
        self.weather_intensity = 0.0  # 0-1
    
    def set_biome(self, biome_id: str) -> None:
        """Set current biome for appropriate effects."""
        self.current_biome = biome_id
        
        # Adjust fog based on biome
        if biome_id == "toxic_plains":
            self.fog_effect.set_intensity(0.4)
            self.fog_effect.color = (100, 150, 80)
        elif biome_id == "crystal_desert":
            self.fog_effect.set_intensity(0.2)
            self.fog_effect.color = (150, 150, 100)
        elif biome_id == "fungal_cave":
            self.fog_effect.set_intensity(0.5)
            self.fog_effect.color = (80, 100, 120)
        elif biome_id == "void_ruins":
            self.fog_effect.set_intensity(0.6)
            self.fog_effect.color = (50, 50, 80)
    
    def trigger_ambient_weather(self, intensity: float = 1.0) -> None:
        """Trigger ambient weather effects."""
        if self.current_biome == "void_ruins":
            self.meteor_rain.trigger(duration=5.0, intensity=intensity)
    
    def add_parallax_layer(self, image: pygame.Surface, depth: float = 1.0) -> None:
        """Add a parallax background layer."""
        layer = ParallaxLayer(image, depth)
        self.parallax_layers.append(layer)
    
    def update(self, dt: float, camera_x: float, camera_y: float) -> None:
        """Update all environmental effects."""
        for layer in self.parallax_layers:
            layer.update(camera_x, camera_y)
        
        self.ambient_particles.update(dt)
        self.fog_effect.update(dt)
        self.meteor_rain.update(dt)
    
    def render(self, surface: pygame.Surface) -> None:
        """Render all environmental effects."""
        # Render parallax backgrounds first
        for layer in self.parallax_layers:
            layer.render(surface, self.screen_width, self.screen_height)
        
        # Render ambient effects
        self.ambient_particles.render(surface)
        self.fog_effect.render(surface)
        self.meteor_rain.render(surface)
    
    def render_above_world(self, surface: pygame.Surface) -> None:
        """Render effects that should appear above world but below UI."""
        # This is for effects that should be layered between world and UI
        pass
