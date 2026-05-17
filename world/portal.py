from __future__ import annotations

import math
import os
import time
from dataclasses import dataclass

import pygame


@dataclass
class PortalRequirement:
    required_item: str | None = None
    required_count: int = 0
    required_flag: str | None = None


class PortalAnimation:
    """Handles animated portal sprite from a sequence of frames."""
    
    _shared_frames: list[pygame.Surface] | None = None
    _shared_frames_locked: list[pygame.Surface] | None = None
    
    @classmethod
    def _load_shared_frames(cls) -> None:
        """Load portal animation frames once (shared across all portals)."""
        if cls._shared_frames is not None:
            return
        
        portal_dir = os.path.join("assets", "images", "portal")
        cls._shared_frames = []
        cls._shared_frames_locked = []
        
        # Load frames in order: portal_01.png .. portal_07.png
        frame_files = sorted([
            f for f in os.listdir(portal_dir)
            if f.lower().endswith(".png") and f.startswith("portal_")
        ])
        
        for fname in frame_files:
            path = os.path.join(portal_dir, fname)
            try:
                surf = pygame.image.load(path).convert_alpha()
                cls._shared_frames.append(surf)
                
                # Create a desaturated/dimmed version for locked portals
                locked = surf.copy()
                dark_overlay = pygame.Surface(locked.get_size(), pygame.SRCALPHA)
                dark_overlay.fill((0, 0, 0, 140))
                locked.blit(dark_overlay, (0, 0))
                cls._shared_frames_locked.append(locked)
            except Exception as e:
                print(f"Failed to load portal frame {path}: {e}")
        
        if not cls._shared_frames:
            print("No portal frames loaded!")
    
    def __init__(self):
        self._load_shared_frames()
        self.frame_index: float = 0.0
        self.frame_speed: float = 8.0  # frames per second
        self.scale: float = 2.0
    
    def update(self, dt: float) -> None:
        """Advance animation frame."""
        if not self._shared_frames:
            return
        self.frame_index += self.frame_speed * dt
        if self.frame_index >= len(self._shared_frames):
            self.frame_index -= len(self._shared_frames)
    
    def get_frame(self, unlocked: bool) -> pygame.Surface | None:
        """Get the current animation frame."""
        frames = self._shared_frames if unlocked else self._shared_frames_locked
        if not frames:
            return None
        idx = int(self.frame_index) % len(frames)
        return frames[idx]


class Portal:
    def __init__(
        self,
        portal_id: str,
        x: float,
        y: float,
        target_world: str,
        requirement: PortalRequirement | None = None,
    ):
        self.portal_id = portal_id
        self.x = float(x)
        self.y = float(y)
        self.target_world = target_world
        self.requirement = requirement or PortalRequirement()

        self.radius = 32
        self.is_unlocked = False
        self.is_active = False
        
        # Animation
        self.anim = PortalAnimation()

    def distance_to(self, x: float, y: float) -> float:
        return math.hypot(self.x - x, self.y - y)

    def can_activate(self, progression_flags: dict[str, bool], inventory) -> bool:
        if self.requirement.required_flag and not progression_flags.get(self.requirement.required_flag, False):
            return False
        if self.requirement.required_item:
            return inventory.count_item(self.requirement.required_item) >= self.requirement.required_count
        return True

    def try_unlock(self, progression_manager, inventory, progression_flags: dict[str, bool] | None = None) -> bool:
        if self.is_unlocked:
            return True

        if progression_flags is None:
            progression_flags = {}

        if self.requirement.required_flag and not progression_flags.get(self.requirement.required_flag, False):
            return False
        
        # Use progression manager to check if this portal's target world can be unlocked
        if not progression_manager.can_unlock_world(self.target_world):
            return False

        # Handle item consumption if required
        if self.requirement.required_item and self.requirement.required_count > 0:
            if inventory.count_item(self.requirement.required_item) < self.requirement.required_count:
                return False
            inventory.remove_item(self.requirement.required_item, self.requirement.required_count)

        self.is_unlocked = True
        self.is_active = True
        return True

    def render(self, surface: pygame.Surface, offset_x: int, offset_y: int, debug: bool) -> None:
        sx = int(self.x - offset_x)
        sy = int(self.y - offset_y)
        
        # Get animated sprite frame
        frame = self.anim.get_frame(self.is_unlocked)
        
        if frame is not None:
            # Scale the frame
            scale = self.anim.scale
            # Add pulsing scale effect for unlocked portals
            if self.is_unlocked:
                pulse = math.sin(time.time() * 3) * 0.1
                scale += pulse
            
            fw = int(frame.get_width() * scale)
            fh = int(frame.get_height() * scale)
            scaled = pygame.transform.smoothscale(frame, (fw, fh))
            
            # Center on portal position
            surface.blit(scaled, (sx - fw // 2, sy - fh // 2))
        else:
            # Fallback: draw circle if no sprites loaded
            pulse = math.sin(time.time() * 3) * 5
            current_radius = self.radius + pulse
            color = (70, 220, 240) if self.is_unlocked else (120, 120, 140)
            pygame.draw.circle(surface, color, (sx, sy), int(current_radius), 3)
            if self.is_unlocked:
                pygame.draw.circle(surface, (100, 255, 255), (sx, sy), int(current_radius * 0.6), 1)
        
        # Target world label
        font = pygame.font.SysFont("segoeui", 14)
        label_color = (180, 230, 255) if self.is_unlocked else (100, 100, 120)
        label = font.render(self.target_world.replace("_", " ").title(), True, label_color)
        label_rect = label.get_rect(center=(sx, sy + 50))
        surface.blit(label, label_rect)
        
        # Interaction hint when unlocked
        if self.is_unlocked:
            hint_font = pygame.font.SysFont("segoeui", 12)
            hint = hint_font.render("[F] Enter", True, (150, 200, 230))
            hint_rect = hint.get_rect(center=(sx, sy + 65))
            surface.blit(hint, hint_rect)
            
        if debug:
            pygame.draw.circle(surface, (220, 220, 255), (sx, sy), self.radius + 20, 1)


class PortalManager:
    def __init__(self):
        self.portals: list[Portal] = []

    def set_portals(self, portals: list[Portal]) -> None:
        self.portals = portals

    def get_near_portal(self, x: float, y: float, interaction_range: float = 72.0) -> Portal | None:
        nearest = None
        nearest_dist = 10_000.0
        for portal in self.portals:
            dist = portal.distance_to(x, y)
            if dist <= interaction_range and dist < nearest_dist:
                nearest = portal
                nearest_dist = dist
        return nearest

    def update(self, dt: float) -> None:
        """Update all portal animations."""
        for portal in self.portals:
            portal.anim.update(dt)

    def render(self, surface: pygame.Surface, offset_x: int, offset_y: int, debug: bool) -> None:
        for portal in self.portals:
            portal.render(surface, offset_x, offset_y, debug)

    def to_save_data(self) -> list[dict]:
        return [
            {
                "portal_id": p.portal_id,
                "target_world": p.target_world,
                "x": p.x,
                "y": p.y,
                "unlocked": p.is_unlocked,
                "active": p.is_active,
            }
            for p in self.portals
        ]

    def apply_save_data(self, entries: list[dict]) -> None:
        by_id = {p.portal_id: p for p in self.portals}
        for entry in entries:
            pid = entry.get("portal_id")
            if pid in by_id:
                by_id[pid].is_unlocked = bool(entry.get("unlocked", False))
                by_id[pid].is_active = bool(entry.get("active", False))
