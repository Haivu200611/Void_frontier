"""
Objective System
Tracks and provides current objectives
"""
import pygame
from settings import *

class ObjectiveSystem:
    def __init__(self, progression_manager):
        self.progression_manager = progression_manager
        
    def get_current_objective(self) -> str:
        """Get the current string for the objective UI based on progression manager"""
        return self.progression_manager.get_current_objective()

    def render_ui(self, surface, font, x, y):
        obj_text = self.get_current_objective()
        text_surf = font.render(f"Objective: {obj_text}", True, (255, 255, 0))
        surface.blit(text_surf, (x, y))
        
    def update(self, dt: float):
        # Future: Add timed objectives or dynamic updates
        pass

