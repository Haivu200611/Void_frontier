"""
Screen effects system.
Handles camera shake, hit flash, damage flash, and other screen-space effects.
"""

import pygame
import random
import math
from typing import Optional


class ScreenShake:
    """Camera shake effect."""
    
    def __init__(self):
        self.intensity: float = 0.0
        self.duration: float = 0.0
        self.max_intensity: float = 0.0
        self.start_time: float = 0.0
        self.active: bool = False
    
    def trigger(self, intensity: float, duration: float) -> None:
        """Trigger a shake effect."""
        self.intensity = max(self.intensity, intensity)
        self.duration = max(self.duration, duration)
        self.max_intensity = intensity
        self.start_time = 0.0
        self.active = True
    
    def update(self, dt: float) -> None:
        """Update shake."""
        if not self.active:
            return
        
        self.start_time += dt
        if self.start_time >= self.duration:
            self.active = False
            self.intensity = 0.0
            return
        
        # Decay intensity over time
        progress = self.start_time / self.duration
        self.intensity = self.max_intensity * (1.0 - progress)
    
    def get_offset(self) -> tuple:
        """Get current shake offset."""
        if not self.active or self.intensity <= 0:
            return (0, 0)
        
        angle = random.uniform(0, 2 * math.pi)
        magnitude = random.uniform(0, self.intensity)
        
        x = math.cos(angle) * magnitude
        y = math.sin(angle) * magnitude
        
        return (x, y)


class HitFlash:
    """Hit flash effect (brief color overlay)."""
    
    def __init__(self):
        self.active: bool = False
        self.duration: float = 0.0
        self.elapsed: float = 0.0
        self.color: tuple = (255, 255, 255)
        self.alpha: int = 255
    
    def trigger(self, color: tuple = (255, 255, 255), duration: float = 0.1) -> None:
        """Trigger a hit flash."""
        self.active = True
        self.duration = duration
        self.elapsed = 0.0
        self.color = color
        self.alpha = 200
    
    def update(self, dt: float) -> None:
        """Update flash."""
        if not self.active:
            return
        
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.active = False
            return
        
        # Fade out flash
        progress = self.elapsed / self.duration
        self.alpha = int(200 * (1.0 - progress))
    
    def render(self, surface: pygame.Surface) -> None:
        """Render flash overlay."""
        if not self.active or self.alpha <= 0:
            return
        
        overlay = pygame.Surface(surface.get_size())
        overlay.fill(self.color)
        overlay.set_alpha(self.alpha)
        surface.blit(overlay, (0, 0))


class DamageFlash:
    """Flash effect when taking damage."""
    
    def __init__(self):
        self.active: bool = False
        self.duration: float = 0.0
        self.elapsed: float = 0.0
        self.flash_alpha: float = 0.0
    
    def trigger(self, duration: float = 0.2) -> None:
        """Trigger damage flash."""
        self.active = True
        self.duration = duration
        self.elapsed = 0.0
        self.flash_alpha = 0.5
    
    def update(self, dt: float) -> None:
        """Update flash."""
        if not self.active:
            return
        
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.active = False
            return
        
        # Pulse effect
        progress = self.elapsed / self.duration
        self.flash_alpha = 0.5 * math.sin(progress * math.pi)
    
    def render(self, surface: pygame.Surface) -> None:
        """Render damage flash overlay."""
        if not self.active or self.flash_alpha <= 0:
            return
        
        overlay = pygame.Surface(surface.get_size())
        overlay.fill((255, 0, 0))
        overlay.set_alpha(int(255 * self.flash_alpha))
        surface.blit(overlay, (0, 0))


class SlowMotion:
    """Slow motion effect."""
    
    def __init__(self):
        self.active: bool = False
        self.time_scale: float = 1.0
        self.duration: float = 0.0
        self.elapsed: float = 0.0
        self.target_scale: float = 0.5
    
    def trigger(self, scale: float = 0.3, duration: float = 0.15) -> None:
        """Trigger slow motion."""
        self.active = True
        self.target_scale = scale
        self.duration = duration
        self.elapsed = 0.0
        self.time_scale = scale
    
    def update(self, dt: float) -> None:
        """Update slow motion."""
        if not self.active:
            self.time_scale = 1.0
            return
        
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.active = False
            self.time_scale = 1.0
            return
        
        # Maintain slow motion
        self.time_scale = self.target_scale


class ScreenEffects:
    """
    Master screen effects controller.
    Coordinates camera shake, flashes, and other screen-space effects.
    """
    
    def __init__(self):
        self.shake = ScreenShake()
        self.hit_flash = HitFlash()
        self.damage_flash = DamageFlash()
        self.slow_motion = SlowMotion()
    
    def trigger_hit(self, intensity: float = 6.0, duration: float = 0.1,
                   flash_color: tuple = (255, 200, 200)) -> None:
        """Trigger full hit effect (shake + flash)."""
        self.shake.trigger(intensity, duration)
        self.hit_flash.trigger(flash_color, duration)
    
    def trigger_heavy_hit(self, intensity: float = 10.0, duration: float = 0.2) -> None:
        """Trigger heavy impact effect."""
        self.shake.trigger(intensity, duration)
        self.hit_flash.trigger((255, 100, 100), duration)
        self.slow_motion.trigger(0.2, 0.15)
    
    def trigger_critical_hit(self, intensity: float = 12.0, duration: float = 0.25) -> None:
        """Trigger critical hit effect."""
        self.shake.trigger(intensity, duration)
        self.hit_flash.trigger((255, 200, 0), duration)
        self.damage_flash.trigger(duration)
        self.slow_motion.trigger(0.1, 0.2)
    
    def trigger_damage_taken(self, intensity: float = 4.0, duration: float = 0.15) -> None:
        """Trigger damage taken feedback."""
        self.shake.trigger(intensity, duration)
        self.damage_flash.trigger(duration)
    
    def trigger_explosion(self, intensity: float = 15.0, duration: float = 0.3) -> None:
        """Trigger explosion effect."""
        self.shake.trigger(intensity, duration)
        self.hit_flash.trigger((255, 150, 50), duration * 0.8)
        self.slow_motion.trigger(0.3, 0.2)
    
    def update(self, dt: float) -> None:
        """Update all effects."""
        # Scale dt by slow motion
        scaled_dt = dt * self.slow_motion.time_scale
        
        self.shake.update(scaled_dt)
        self.hit_flash.update(scaled_dt)
        self.damage_flash.update(scaled_dt)
        self.slow_motion.update(dt)  # Update slow motion with real dt
    
    def render(self, surface: pygame.Surface) -> None:
        """Render all screen overlays."""
        self.hit_flash.render(surface)
        self.damage_flash.render(surface)
    
    def get_shake_offset(self) -> tuple:
        """Get current camera shake offset."""
        return self.shake.get_offset()
    
    def get_time_scale(self) -> float:
        """Get current time scale from slow motion."""
        return self.slow_motion.time_scale
