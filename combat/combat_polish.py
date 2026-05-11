"""
Combat polish and feedback system.
Adds visual and audio feedback for combat actions.
"""

from typing import Optional, Tuple
import math


class AttackTrail:
    """Visual trail effect for attacks."""
    
    def __init__(self, start_x: float, start_y: float, end_x: float, end_y: float,
                 color: Tuple[int, int, int] = (200, 100, 50), lifetime: float = 0.1):
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = end_x
        self.end_y = end_y
        self.color = color
        self.lifetime = lifetime
        self.age = 0.0
        self.width = 8
    
    def update(self, dt: float) -> bool:
        """Update trail. Return True if still alive."""
        self.age += dt
        
        # Fade out
        progress = self.age / self.lifetime
        self.width = max(1, int(8 * (1.0 - progress)))
        
        return self.age < self.lifetime
    
    def render(self, surface, offset_x: float, offset_y: float) -> None:
        """Render trail."""
        import pygame
        
        screen_x1 = int(self.start_x - offset_x)
        screen_y1 = int(self.start_y - offset_y)
        screen_x2 = int(self.end_x - offset_x)
        screen_y2 = int(self.end_y - offset_y)
        
        # Calculate alpha based on age
        alpha = int(255 * (1.0 - self.age / self.lifetime))
        
        # Create temporary surface for alpha blending
        trail_surface = pygame.Surface((max(abs(screen_x2 - screen_x1), 1), 
                                      max(abs(screen_y2 - screen_y1), 1)), 
                                     pygame.SRCALPHA)
        
        # Draw trail line with gradient
        pygame.draw.line(trail_surface, (*self.color, alpha), 
                        (0, 0), (screen_x2 - screen_x1, screen_y2 - screen_y1), self.width)


class CriticalHitEffect:
    """Critical hit visual effect."""
    
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.age = 0.0
        self.lifetime = 0.3
        self.scale = 0.0
    
    def update(self, dt: float) -> bool:
        """Update effect. Return True if still alive."""
        self.age += dt
        progress = self.age / self.lifetime
        
        # Pulse scale
        self.scale = math.sin(progress * math.pi) * 2.0
        
        return self.age < self.lifetime
    
    def render(self, surface, offset_x: float, offset_y: float) -> None:
        """Render critical hit effect."""
        import pygame
        
        screen_x = int(self.x - offset_x)
        screen_y = int(self.y - offset_y)
        
        progress = self.age / self.lifetime
        alpha = int(255 * (1.0 - progress))
        
        # Draw expanding circle
        size = int(50 + self.scale * 50)
        circle_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.circle(circle_surface, (255, 200, 0, alpha), (size, size), size)
        
        surface.blit(circle_surface, (screen_x - size, screen_y - size))
        
        # Draw star burst
        for i in range(4):
            angle = math.pi / 2 * i
            x_end = screen_x + math.cos(angle) * 80 * progress
            y_end = screen_y + math.sin(angle) * 80 * progress
            pygame.draw.line(surface, (255, 200, 0, alpha), (screen_x, screen_y),
                           (int(x_end), int(y_end)), 2)


class CombatPolishSystem:
    """
    Manages all combat visual and audio feedback.
    Tracks attack trails, critical hits, knockback effects, etc.
    """
    
    def __init__(self):
        self.trails = []
        self.critical_hits = []
        self.hit_freeze_time = 0.0
        self.max_hit_freeze = 0.05  # 50ms freeze on hit
    
    def spawn_attack_trail(self, start_x: float, start_y: float, end_x: float, end_y: float,
                          color: Tuple[int, int, int] = (200, 100, 50),
                          lifetime: float = 0.1) -> None:
        """Spawn an attack trail effect."""
        trail = AttackTrail(start_x, start_y, end_x, end_y, color, lifetime)
        self.trails.append(trail)
    
    def spawn_critical_hit(self, x: float, y: float) -> None:
        """Spawn a critical hit effect."""
        effect = CriticalHitEffect(x, y)
        self.critical_hits.append(effect)
    
    def trigger_hit_freeze(self, duration: float = 0.05) -> None:
        """Trigger a hit freeze frame effect."""
        self.hit_freeze_time = duration
    
    def on_hit(self, attacker_x: float, attacker_y: float, defender_x: float, defender_y: float,
              is_critical: bool = False, damage: float = 0) -> None:
        """
        Called when an attack hits.
        Creates appropriate visual feedback.
        """
        # Spawn attack trail
        self.spawn_attack_trail(attacker_x, attacker_y, defender_x, defender_y,
                               color=(255, 100, 100))
        
        # Spawn critical hit effect if critical
        if is_critical:
            self.spawn_critical_hit(defender_x, defender_y)
            self.trigger_hit_freeze(0.1)
        else:
            self.trigger_hit_freeze(0.03)
    
    def on_dodge(self, dodge_x: float, dodge_y: float) -> None:
        """Called when attack is dodged."""
        # Spawn dodge effect
        pass
    
    def on_block(self, block_x: float, block_y: float) -> None:
        """Called when attack is blocked."""
        # Spawn block effect
        pass
    
    def on_projectile_hit(self, projectile_x: float, projectile_y: float) -> None:
        """Called when projectile hits."""
        self.spawn_attack_trail(projectile_x, projectile_y,
                               projectile_x - 50, projectile_y - 50,
                               color=(100, 200, 255))
    
    def update(self, dt: float) -> None:
        """Update all combat effects."""
        # Update trails
        self.trails = [t for t in self.trails if t.update(dt)]
        
        # Update critical hits
        self.critical_hits = [c for c in self.critical_hits if c.update(dt)]
        
        # Update hit freeze
        if self.hit_freeze_time > 0:
            self.hit_freeze_time -= dt
    
    def render(self, surface, offset_x: float, offset_y: float) -> None:
        """Render all combat effects."""
        for trail in self.trails:
            trail.render(surface, offset_x, offset_y)
        
        for critical in self.critical_hits:
            critical.render(surface, offset_x, offset_y)
    
    def get_time_scale(self) -> float:
        """Get time scale for hit freeze effect."""
        if self.hit_freeze_time > 0:
            return 0.1  # 10% speed during hit freeze
        return 1.0


class KnockbackPolish:
    """Polish knockback with better feel."""
    
    @staticmethod
    def calculate_knockback(attacker_x: float, attacker_y: float,
                           defender_x: float, defender_y: float,
                           base_force: float,
                           is_critical: bool = False) -> Tuple[float, float]:
        """
        Calculate knockback direction and force.
        
        :return: (knockback_x, knockback_y)
        """
        dx = defender_x - attacker_x
        dy = defender_y - attacker_y
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance <= 0:
            return (0, 0)
        
        # Normalize direction
        nx = dx / distance
        ny = dy / distance
        
        # Apply force (increased for critical)
        force = base_force * 120  # Scale to pixels/second
        if is_critical:
            force *= 1.5
        
        # Add small upward bias for knockup effect
        knockback_x = nx * force
        knockback_y = ny * force - 100
        
        return (knockback_x, knockback_y)


class RecoilEffect:
    """Weapon recoil effect."""
    
    def __init__(self, intensity: float = 1.0):
        self.intensity = intensity
        self.recoil_x = 0.0
        self.recoil_y = 0.0
    
    def trigger(self, direction_x: float, direction_y: float) -> None:
        """Trigger recoil."""
        # Opposite direction of attack
        mag = math.sqrt(direction_x * direction_x + direction_y * direction_y)
        if mag > 0:
            self.recoil_x = -(direction_x / mag) * self.intensity * 50
            self.recoil_y = -(direction_y / mag) * self.intensity * 50
    
    def update(self, dt: float, friction: float = 0.85) -> None:
        """Update recoil."""
        self.recoil_x *= friction
        self.recoil_y *= friction
        
        # Snap to zero
        if abs(self.recoil_x) < 0.5:
            self.recoil_x = 0
        if abs(self.recoil_y) < 0.5:
            self.recoil_y = 0
    
    def get_offset(self) -> Tuple[float, float]:
        """Get current recoil offset."""
        return (self.recoil_x, self.recoil_y)
