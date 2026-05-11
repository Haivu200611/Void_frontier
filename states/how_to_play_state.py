import pygame
from core.state_machine import State
from settings import *
from ui.background import SpaceBackground

class HowToPlayState(State):
    def enter(self, **kwargs):
        self.font_title = pygame.font.SysFont("impact", 60)
        self.font_text = pygame.font.SysFont("arial", 30)
        self.background = SpaceBackground()
        
        self.instructions = [
            "HOW TO PLAY",
            "",
            "WASD = Move",
            "Left Mouse = Attack",
            "Shift + Left Mouse = Mine Ore",
            "Right Mouse = Shoot",
            "1-9 = Hotbar Slots",
            "R = Use Consumable",
            "E = Inventory / Drag & Drop",
            "C = Crafting",
            "F = Portal Interact",
            "F5/F9 = Save / Load",
            "P = Toggle Auto Mode",
            "",
            "Press ESC to go back."
        ]
        
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.engine.state_machine.change_state("Menu")
                    
    def update(self, dt):
        self.background.update(dt)
        
    def render(self, surface):
        self.background.render(surface)
        
        # Draw a translucent panel
        panel = pygame.Surface((WINDOW_WIDTH - 200, WINDOW_HEIGHT - 100), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 180))
        surface.blit(panel, (100, 50))
        
        for i, line in enumerate(self.instructions):
            color = COLOR_PORTAL if i == 0 else COLOR_TEXT
            font = self.font_title if i == 0 else self.font_text
            text_surf = font.render(line, True, color)
            text_rect = text_surf.get_rect(center=(WINDOW_WIDTH//2, 100 + i * 40))
            surface.blit(text_surf, text_rect)
