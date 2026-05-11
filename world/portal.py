from __future__ import annotations

import math
from dataclasses import dataclass

import pygame


@dataclass
class PortalRequirement:
    required_item: str | None = None
    required_count: int = 0
    required_flag: str | None = None


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

    def distance_to(self, x: float, y: float) -> float:
        return math.hypot(self.x - x, self.y - y)

    def can_activate(self, progression_flags: dict[str, bool], inventory) -> bool:
        if self.requirement.required_flag and not progression_flags.get(self.requirement.required_flag, False):
            return False
        if self.requirement.required_item:
            return inventory.count_item(self.requirement.required_item) >= self.requirement.required_count
        return True

    def try_unlock(self, progression_manager, inventory) -> bool:
        if self.is_unlocked:
            return True
        
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
        
        # Animation: Pulsing radius
        import math, time
        pulse = math.sin(time.time() * 3) * 5
        current_radius = self.radius + pulse
        
        color = (70, 220, 240) if self.is_unlocked else (120, 120, 140)
        pygame.draw.circle(surface, color, (sx, sy), int(current_radius), 3)
        
        if self.is_unlocked:
            # Inner glow
            pygame.draw.circle(surface, (100, 255, 255), (sx, sy), int(current_radius * 0.6), 1)
            
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
