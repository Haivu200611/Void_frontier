"""
Particle emitters for complex visual patterns.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from particles.particle_system import ParticleSystem

class ParticleEmitter:
    """Emits particles in a pattern."""
    
    def __init__(self, x: float, y: float, particle_pool: 'ParticleSystem'):
        self.x = x
        self.y = y
        self.pool = particle_pool
        self.active = True
        self.duration = 0.1
        self.age = 0.0
        
    def update(self, dt: float) -> None:
        """Update emitter."""
        if not self.active:
            return
        
        self.age += dt
        if self.age >= self.duration:
            self.active = False
    
    def emit(self) -> None:
        """Emit particles - override in subclass."""
        pass

class HitEmitter(ParticleEmitter):
    def emit(self) -> None:
        if self.active:
            self.pool.spawn_hit_particles(self.x, self.y)

class ExplosionEmitter(ParticleEmitter):
    def emit(self) -> None:
        if self.active:
            self.pool.spawn_explosion_particles(self.x, self.y)
