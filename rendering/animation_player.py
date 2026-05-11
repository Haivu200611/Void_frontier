"""
Animation system for sprite-based animations.
Handles animation sequences, playback, looping, and events.
"""

import pygame
from typing import Dict, List, Optional, Callable
from enum import Enum


class AnimationState(Enum):
    """Animation playback states."""
    IDLE = "idle"
    PLAYING = "playing"
    PAUSED = "paused"
    STOPPED = "stopped"


class Frame:
    """Single frame in an animation."""
    
    def __init__(self, sprite: pygame.Surface, duration: float, event: Optional[Callable] = None):
        """
        :param sprite: Pygame surface for this frame
        :param duration: Time to display frame (seconds)
        :param event: Optional callback when frame plays
        """
        self.sprite = sprite
        self.duration = duration
        self.event = event


class Animation:
    """A sequence of animation frames."""
    
    def __init__(self, name: str, frames: List[Frame], loop: bool = True, speed: float = 1.0):
        """
        :param name: Animation name (e.g., "idle", "run", "attack")
        :param frames: List of Frame objects
        :param loop: Whether animation loops
        :param speed: Playback speed multiplier
        """
        self.name = name
        self.frames = frames
        self.loop = loop
        self.speed = speed
        self.total_duration = sum(f.duration for f in frames)
    
    def get_frame_at(self, time: float) -> Frame:
        """Get frame at specific time in animation."""
        if self.total_duration <= 0:
            return self.frames[0] if self.frames else None
        
        # Wrap time if looping
        if self.loop:
            time = time % self.total_duration
        else:
            time = min(time, self.total_duration)
        
        # Find frame
        elapsed = 0
        for frame in self.frames:
            elapsed += frame.duration
            if time <= elapsed:
                return frame
        
        return self.frames[-1] if self.frames else None


class AnimationPlayer:
    """
    Plays and manages animations.
    Supports:
    - Multiple animations
    - Looping and one-shot
    - Animation transitions
    - Frame events
    - Speed scaling
    """
    
    def __init__(self):
        self.animations: Dict[str, Animation] = {}
        self.current_animation: Optional[Animation] = None
        self.previous_animation: Optional[Animation] = None
        
        self.state = AnimationState.IDLE
        self.current_time: float = 0.0
        self.speed_multiplier: float = 1.0
        
        self.on_animation_end: Optional[Callable] = None
        self._last_frame_index: int = -1
    
    def add_animation(self, animation: Animation) -> None:
        """Register an animation."""
        self.animations[animation.name] = animation
    
    def play(self, name: str, restart: bool = False) -> bool:
        """
        Play an animation by name.
        
        :param name: Animation name
        :param restart: Force restart even if already playing
        :return: True if animation started
        """
        if name not in self.animations:
            print(f"Animation '{name}' not found")
            return False
        
        animation = self.animations[name]
        
        # Don't restart same animation unless forced
        if self.current_animation == animation and not restart:
            if self.state == AnimationState.PAUSED:
                self.state = AnimationState.PLAYING
            return True
        
        # Transition to new animation
        self.previous_animation = self.current_animation
        self.current_animation = animation
        self.current_time = 0.0
        self._last_frame_index = -1
        self.state = AnimationState.PLAYING
        
        return True
    
    def pause(self) -> None:
        """Pause current animation."""
        if self.state == AnimationState.PLAYING:
            self.state = AnimationState.PAUSED
    
    def resume(self) -> None:
        """Resume paused animation."""
        if self.state == AnimationState.PAUSED:
            self.state = AnimationState.PLAYING
    
    def stop(self) -> None:
        """Stop animation."""
        self.state = AnimationState.STOPPED
        self.current_animation = None
        self.current_time = 0.0
    
    def update(self, dt: float) -> None:
        """Update animation playback."""
        if self.state != AnimationState.PLAYING or self.current_animation is None:
            return
        
        # Apply speed
        self.current_time += dt * self.speed_multiplier * self.current_animation.speed
        
        # Check if animation finished
        if not self.current_animation.loop and self.current_time >= self.current_animation.total_duration:
            self.state = AnimationState.STOPPED
            if self.on_animation_end:
                self.on_animation_end(self.current_animation.name)
        
        # Check for frame events
        frame_index = self._get_current_frame_index()
        if frame_index != self._last_frame_index:
            frame = self.current_animation.frames[frame_index]
            if frame.event:
                frame.event()
            self._last_frame_index = frame_index
    
    def _get_current_frame_index(self) -> int:
        """Get index of current frame."""
        if not self.current_animation or not self.current_animation.frames:
            return 0
        
        time = self.current_time
        if self.current_animation.loop:
            time = time % self.current_animation.total_duration
        else:
            time = min(time, self.current_animation.total_duration)
        
        elapsed = 0
        for i, frame in enumerate(self.current_animation.frames):
            elapsed += frame.duration
            if time <= elapsed:
                return i
        
        return len(self.current_animation.frames) - 1
    
    def get_current_sprite(self) -> Optional[pygame.Surface]:
        """Get current frame sprite."""
        if not self.current_animation:
            return None
        
        frame_index = self._get_current_frame_index()
        if 0 <= frame_index < len(self.current_animation.frames):
            return self.current_animation.frames[frame_index].sprite
        
        return None
    
    def get_current_animation(self) -> Optional[str]:
        """Get name of current animation."""
        return self.current_animation.name if self.current_animation else None
    
    def is_playing(self, name: Optional[str] = None) -> bool:
        """Check if animation is playing."""
        if self.state != AnimationState.PLAYING:
            return False
        
        if name is None:
            return True
        
        return self.current_animation and self.current_animation.name == name
    
    def get_progress(self) -> float:
        """Get animation progress (0.0 to 1.0)."""
        if not self.current_animation or self.current_animation.total_duration <= 0:
            return 0.0
        
        progress = self.current_time / self.current_animation.total_duration
        if self.current_animation.loop:
            progress = progress % 1.0
        else:
            progress = min(progress, 1.0)
        
        return progress
