import pygame
from core.state_machine import State
from settings import *

class EndingState(State):
    def enter(self, **kwargs):
        self.font = pygame.font.SysFont(None, 48)
        self.sub_font = pygame.font.SysFont(None, 24)
        self.timer = 0.0
        
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                if self.timer > 2.0:
                    self.engine.state_machine.change_state("Menu")
                    
    def update(self, dt):
        self.timer += dt
        
    def render(self, surface):
        surface.fill((10, 10, 20))
        
        # Center text
        title = self.font.render("MISSION ACCOMPLISHED", True, (200, 255, 200))
        title_rect = title.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 50))
        surface.blit(title, title_rect)
        
        desc = self.sub_font.render("ORION-7 has escaped the Void Frontier.", True, (150, 200, 150))
        desc_rect = desc.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 20))
        surface.blit(desc, desc_rect)
        
        if self.timer > 3.0:
            prompt = self.sub_font.render("Press any key to return to main menu", True, (100, 100, 100))
            prompt_rect = prompt.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 100))
            surface.blit(prompt, prompt_rect)
