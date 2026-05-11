"""
Boss Arena System
Defines boss zones and arena hazards
"""
import pygame
from settings import *
from typing import List, Tuple, Optional


class BossArena:
    """
    Defines a specific area for boss fights
    """
    def __init__(self, x: float, y: float, width: float, height: float, world_id: str):
        self.rect = pygame.Rect(x, y, width, height)
        self.world_id = world_id
        self.is_active = False
        self.hazards: List[Tuple[float, float, float, str]] = []  # x, y, radius, type
        
    def activate(self) -> None:
        self.is_active = True
        
    def deactivate(self) -> None:
        self.is_active = False
        
    def add_hazard(self, x: float, y: float, radius: float, hazard_type: str) -> None:
        self.hazards.append((x, y, radius, hazard_type))
        
    def render(self, surface: pygame.Surface, ox: int, oy: int, debug: bool) -> None:
        if not self.is_active:
            return
            
        # Render arena boundary with a glowing effect
        arena_rect = self.rect.move(-ox, -oy)
        pygame.draw.rect(surface, (200, 0, 0), arena_rect, 2)
        
        # Draw hazard zones
        for hx, hy, hr, htype in self.hazards:
            color = (255, 0, 0, 100) if htype == "toxic" else (255, 255, 0, 100)
            # Create a surface for transparency
            s = pygame.Surface((int(hr*2), int(hr*2)), pygame.SRCALPHA)
            pygame.draw.circle(s, color, (int(hr), int(hr)), int(hr))
            surface.blit(s, (int(hx - ox - hr), int(hy - oy - hr)))
        
        if debug:
            for hx, hy, hr, htype in self.hazards:
                pygame.draw.circle(surface, (255, 100, 0), (int(hx - ox), int(hy - oy)), int(hr), 1)
