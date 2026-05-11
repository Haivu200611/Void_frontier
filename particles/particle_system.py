"""
Particle system for visual effects.
Handles particle creation, pooling, updates, and rendering.
"""

import pygame
import random
import math
from typing import List, Tuple, Optional


import pygame
import random
import math
from typing import List, Tuple, Optional

from particles.particle import Particle
from particles.emitters import ParticleEmitter


class ParticleSystem:
    """
    Manages all particles in the game.
    Uses object pooling for efficiency.
    """
    
    def __init__(self, max_particles: int = 1000):
        self.max_particles = max_particles
        self.particles: List[Particle] = [Particle() for _ in range(max_particles)]
        self.active_particles: int = 0
        self.emitters: List[ParticleEmitter] = []
    
    def spawn_particle(self, x: float, y: float, vx: float = 0, vy: float = 0,
                      color: Tuple[int, int, int] = (255, 255, 255),
                      size: float = 4.0, lifetime: float = 1.0,
                      gravity: float = 0, drag: float = 0.98,
                      scale_over_time: bool = False) -> Optional[Particle]:
        """Spawn a single particle."""
        if self.active_particles >= self.max_particles:
            return None
        
        particle = self.particles[self.active_particles]
        particle.x = x
        particle.y = y
        particle.vx = vx
        particle.vy = vy
        particle.color = color
        particle.size = size
        particle.lifetime = lifetime
        particle.age = 0.0
        particle.alpha = 255.0
        particle.active = True
        particle.gravity = gravity
        particle.drag = drag
        particle.scale_over_time = scale_over_time
        
        self.active_particles += 1
        return particle
    
    def spawn_burst(self, x: float, y: float, count: int = 10,
                   speed: float = 100, color: Tuple[int, int, int] = (255, 255, 255),
                   size: float = 4.0, lifetime: float = 0.5,
                   spread: float = 360) -> None:
        """Spawn a burst of particles in random directions."""
        for _ in range(count):
            angle = random.uniform(0, spread)
            rad = math.radians(angle)
            vx = math.cos(rad) * speed
            vy = math.sin(rad) * speed
            
            self.spawn_particle(x, y, vx, vy, color, size, lifetime, drag=0.95)
    
    def spawn_trail(self, start_x: float, start_y: float, end_x: float, end_y: float,
                   count: int = 10, color: Tuple[int, int, int] = (255, 255, 255),
                   size: float = 3.0, lifetime: float = 0.3) -> None:
        """Spawn particles along a line."""
        for i in range(count):
            t = i / max(1, count - 1)
            x = start_x + (end_x - start_x) * t
            y = start_y + (end_y - start_y) * t
            
            offset_x = random.uniform(-10, 10)
            offset_y = random.uniform(-10, 10)
            
            self.spawn_particle(x + offset_x, y + offset_y, 0, 0, color, size, lifetime)
    
    def spawn_mining_particles(self, x: float, y: float) -> None:
        """Spawn particles for mining effect."""
        self.spawn_burst(x, y, count=8, speed=150,
                        color=(200, 200, 150), size=3, lifetime=0.4, spread=180)
    
    def spawn_hit_particles(self, x: float, y: float) -> None:
        """Spawn particles for hit effect."""
        self.spawn_burst(x, y, count=12, speed=200,
                        color=(255, 100, 100), size=5, lifetime=0.3, spread=360)
    
    def spawn_blood_particles(self, x: float, y: float) -> None:
        """Spawn particles for damage effect."""
        self.spawn_burst(x, y, count=15, speed=250,
                        color=(200, 0, 0), size=4, lifetime=0.5, spread=360)
    
    def spawn_explosion_particles(self, x: float, y: float) -> None:
        """Spawn particles for explosion effect."""
        self.spawn_burst(x, y, count=20, speed=300,
                        color=(255, 150, 0), size=6, lifetime=0.6, spread=360)
    
    def spawn_portal_particles(self, x: float, y: float) -> None:
        """Spawn particles for portal effect."""
        self.spawn_burst(x, y, count=25, speed=100,
                        color=(50, 200, 200), size=5, lifetime=0.8, spread=360)
    
    def spawn_toxic_particles(self, x: float, y: float) -> None:
        """Spawn particles for toxic effect."""
        self.spawn_burst(x, y, count=15, speed=80,
                        color=(100, 200, 50), size=4, lifetime=1.0, spread=360)
    
    def spawn_energy_particles(self, x: float, y: float) -> None:
        """Spawn particles for energy effect."""
        self.spawn_burst(x, y, count=20, speed=180,
                        color=(100, 150, 255), size=5, lifetime=0.7, spread=360)
    
    def update(self, dt: float) -> None:
        """Update all particles."""
        # Update particles (only iterate active ones)
        for i in range(self.active_particles):
            self.particles[i].update(dt)
            
            # Move dead particles to end of active list
            if not self.particles[i].active:
                self.particles[i], self.particles[self.active_particles - 1] = \
                    self.particles[self.active_particles - 1], self.particles[i]
                self.active_particles -= 1
        
        # Update emitters
        for emitter in self.emitters[:]:
            emitter.update(dt)
            emitter.emit()
            if not emitter.active:
                self.emitters.remove(emitter)
    
    def render(self, surface: pygame.Surface, offset_x: float, offset_y: float) -> None:
        """Render all active particles."""
        for i in range(self.active_particles):
            self.particles[i].render(surface, offset_x, offset_y)
    
    def clear(self) -> None:
        """Clear all particles."""
        for particle in self.particles:
            particle.active = False
        self.active_particles = 0
        self.emitters.clear()
    
    def get_active_count(self) -> int:
        """Get number of active particles."""
        return self.active_particles

