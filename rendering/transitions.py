"""
Transition effects and cinematics.
Handles fades, screen transitions, and ending sequences.
"""

import pygame
import math
from typing import Optional, Callable


class FadeTransition:
    """Fade in/out transition effect."""
    
    def __init__(self, duration: float = 1.0, fade_in: bool = True,
                on_complete: Optional[Callable] = None):
        self.duration = duration
        self.elapsed = 0.0
        self.fade_in = fade_in
        self.on_complete = on_complete
        self.active = True
    
    def update(self, dt: float) -> bool:
        """Update transition. Return True if complete."""
        if not self.active:
            return False
        
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.active = False
            if self.on_complete:
                self.on_complete()
            return True
        
        return False
    
    def get_alpha(self) -> int:
        """Get current fade alpha (0-255)."""
        progress = self.elapsed / self.duration
        
        if self.fade_in:
            # Fade in: alpha goes from 255 to 0
            return int(255 * (1.0 - progress))
        else:
            # Fade out: alpha goes from 0 to 255
            return int(255 * progress)
    
    def render(self, surface: pygame.Surface) -> None:
        """Render fade overlay."""
        alpha = self.get_alpha()
        if alpha <= 0:
            return
        
        overlay = pygame.Surface(surface.get_size())
        overlay.fill((0, 0, 0))
        overlay.set_alpha(alpha)
        surface.blit(overlay, (0, 0))


class ScaleTransition:
    """Scale/zoom transition effect."""
    
    def __init__(self, duration: float = 1.0, zoom_out: bool = True,
                on_complete: Optional[Callable] = None):
        self.duration = duration
        self.elapsed = 0.0
        self.zoom_out = zoom_out
        self.on_complete = on_complete
        self.active = True
    
    def update(self, dt: float) -> bool:
        """Update transition."""
        if not self.active:
            return False
        
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.active = False
            if self.on_complete:
                self.on_complete()
            return True
        
        return False
    
    def get_scale(self) -> float:
        """Get current scale factor."""
        progress = self.elapsed / self.duration
        
        if self.zoom_out:
            # Zoom out: scale goes from 1.0 to 0.5
            return 1.0 - progress * 0.5
        else:
            # Zoom in: scale goes from 0.5 to 1.0
            return 0.5 + progress * 0.5
    
    def render(self, surface: pygame.Surface, game_surface: pygame.Surface) -> None:
        """Render scaled game view."""
        scale = self.get_scale()
        
        # Create scaled surface
        new_size = (int(game_surface.get_width() * scale),
                   int(game_surface.get_height() * scale))
        scaled = pygame.transform.scale(game_surface, new_size)
        
        # Center on screen
        x = (surface.get_width() - new_size[0]) // 2
        y = (surface.get_height() - new_size[1]) // 2
        
        # Fill background
        surface.fill((0, 0, 0))
        surface.blit(scaled, (x, y))


class SlideTransition:
    """Slide transition effect."""
    
    def __init__(self, duration: float = 1.0, direction: str = "right",
                on_complete: Optional[Callable] = None):
        self.duration = duration
        self.elapsed = 0.0
        self.direction = direction  # "left", "right", "up", "down"
        self.on_complete = on_complete
        self.active = True
    
    def update(self, dt: float) -> bool:
        """Update transition."""
        if not self.active:
            return False
        
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.active = False
            if self.on_complete:
                self.on_complete()
            return True
        
        return False
    
    def get_offset(self, screen_width: int, screen_height: int) -> tuple:
        """Get offset for slide."""
        progress = self.elapsed / self.duration
        
        if self.direction == "right":
            return (-int(screen_width * (1.0 - progress)), 0)
        elif self.direction == "left":
            return (int(screen_width * (1.0 - progress)), 0)
        elif self.direction == "down":
            return (0, -int(screen_height * (1.0 - progress)))
        elif self.direction == "up":
            return (0, int(screen_height * (1.0 - progress)))
        
        return (0, 0)
    
    def render(self, surface: pygame.Surface, game_surface: pygame.Surface) -> None:
        """Render slide transition."""
        offset = self.get_offset(surface.get_width(), surface.get_height())
        
        surface.fill((0, 0, 0))
        surface.blit(game_surface, offset)


class EndingSequence:
    """Ending cinematic sequence."""
    
    def __init__(self, duration: float = 10.0):
        self.duration = duration
        self.elapsed = 0.0
        self.stages = [
            (0.0, "Launch sequence initiated..."),
            (2.0, "Reactor overload detected"),
            (4.0, "Escape pods launching"),
            (6.0, "System shutdown"),
            (8.0, "Farewell, Void Frontier"),
        ]
        self.current_stage = 0
        self.current_text = ""
    
    def update(self, dt: float) -> bool:
        """Update ending sequence."""
        self.elapsed += dt
        
        # Check stage progression
        for stage_time, text in self.stages:
            if self.elapsed >= stage_time and self.current_text != text:
                self.current_text = text
        
        return self.elapsed >= self.duration
    
    def render(self, surface: pygame.Surface) -> None:
        """Render ending sequence."""
        # Background fade
        alpha = min(255, int(self.elapsed * 30))
        overlay = pygame.Surface(surface.get_size())
        overlay.fill((0, 0, 0))
        overlay.set_alpha(alpha)
        surface.blit(overlay, (0, 0))
        
        # Display text
        font = pygame.font.SysFont(None, 36)
        text_surface = font.render(self.current_text, True, (200, 200, 220))
        
        # Center text
        x = (surface.get_width() - text_surface.get_width()) // 2
        y = (surface.get_height() - text_surface.get_height()) // 2
        
        # Fade in text
        text_alpha = min(255, int((self.elapsed % 2.0) * 255))
        text_surface.set_alpha(text_alpha)
        surface.blit(text_surface, (x, y))


class TransitionManager:
    """Manages active transitions."""
    
    def __init__(self):
        self.transitions = []
    
    def add_transition(self, transition) -> None:
        """Add a transition."""
        self.transitions.append(transition)
    
    def fade_out(self, duration: float = 1.0, 
                on_complete: Optional[Callable] = None) -> None:
        """Create a fade out transition."""
        self.add_transition(FadeTransition(duration, False, on_complete))
    
    def fade_in(self, duration: float = 1.0,
               on_complete: Optional[Callable] = None) -> None:
        """Create a fade in transition."""
        self.add_transition(FadeTransition(duration, True, on_complete))
    
    def slide(self, duration: float = 1.0, direction: str = "right",
             on_complete: Optional[Callable] = None) -> None:
        """Create a slide transition."""
        self.add_transition(SlideTransition(duration, direction, on_complete))
    
    def update(self, dt: float) -> None:
        """Update all transitions."""
        for transition in self.transitions[:]:
            if transition.update(dt):
                self.transitions.remove(transition)
    
    def is_transitioning(self) -> bool:
        """Check if any transitions are active."""
        return len(self.transitions) > 0
    
    def render(self, surface: pygame.Surface) -> None:
        """Render all transitions."""
        for transition in self.transitions:
            if isinstance(transition, FadeTransition):
                transition.render(surface)
            elif isinstance(transition, SlideTransition):
                # Need game surface for slide
                pass
