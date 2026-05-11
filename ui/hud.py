"""
HUD system for player status and health bars.
"""

import pygame
from settings import *

class HUD:
    """
    Manages the player's Heads-Up Display.
    Handles health, oxygen, and hunger bars.
    """
    
    def __init__(self):
        self.font = pygame.font.SysFont(None, 22)
        self.hud_x = 12
        self.hud_y = WINDOW_HEIGHT - 110
        self.bar_w = 180
        self.bar_h = 18
        self.padding = 26
        
        # Smooth bar values
        self.display_hp = 0.0
        self.display_o2 = 0.0
        self.display_food = 0.0
        
    def update(self, dt: float, player) -> None:
        """Update smooth bar transitions."""
        self.display_hp += (player.health - self.display_hp) * 5 * dt
        self.display_o2 += (player.oxygen - self.display_o2) * 5 * dt
        self.display_food += (player.hunger - self.display_food) * 5 * dt
        
    def render(self, surface: pygame.Surface, player) -> None:
        """Render HUD elements."""
        bars = [
            ("HP", self.display_hp, player.max_health, (220, 50, 50), (50, 10, 10)),
            ("O2", self.display_o2, player.max_oxygen, (50, 180, 255), (10, 30, 60)),
            ("FOOD", self.display_food, player.max_hunger, (255, 170, 30), (60, 40, 10)),
        ]

        for i, (label, value, max_val, fg, bg) in enumerate(bars):
            by = self.hud_y + i * self.padding
            ratio = max(0.0, value / max_val) if max_val > 0 else 0.0

            # Background shadow
            pygame.draw.rect(surface, bg, (self.hud_x, by, self.bar_w, self.bar_h), border_radius=4)
            # Foreground bar
            pygame.draw.rect(surface, fg, (self.hud_x, by, int(self.bar_w * ratio), self.bar_h), border_radius=4)
            # Border
            pygame.draw.rect(surface, (80, 80, 80), (self.hud_x, by, self.bar_w, self.bar_h), 1, border_radius=4)

            # Text
            text = self.font.render(f"{label}", True, COLOR_TEXT)
            surface.blit(text, (self.hud_x + 8, by + 2))
            
            # Value text on the right
            val_text = self.font.render(f"{int(value)}", True, (255, 255, 255))
            surface.blit(val_text, (self.hud_x + self.bar_w - val_text.get_width() - 8, by + 2))
