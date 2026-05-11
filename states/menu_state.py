import pygame
from core.state_machine import State
from settings import *
from ui.background import SpaceBackground

class MenuState(State):
    def enter(self, **kwargs):
        self.font_title = pygame.font.SysFont("impact", 100)
        self.font_menu = pygame.font.SysFont("arial", 40)
        self.background = SpaceBackground()
        
        self.options = ["START GAME", "HOW TO PLAY", "EXIT"]
        self.selected_index = 0
        
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    self.selected_index = (self.selected_index - 1) % len(self.options)
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    self.selected_index = (self.selected_index + 1) % len(self.options)
                elif event.key == pygame.K_RETURN:
                    self.select_option()
                    
    def select_option(self):
        selected = self.options[self.selected_index]
        if selected == "START GAME":
            self.engine.state_machine.change_state("Play")
        elif selected == "HOW TO PLAY":
            self.engine.state_machine.change_state("HowToPlay")
        elif selected == "EXIT":
            self.engine.running = False
            
    def update(self, dt):
        self.background.update(dt)
        
    def render(self, surface):
        self.background.render(surface)
        
        title_surf = self.font_title.render("VOID FRONTIER", True, COLOR_PORTAL)
        title_rect = title_surf.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//4))
        surface.blit(title_surf, title_rect)
        
        for i, option in enumerate(self.options):
            color = COLOR_PLAYER if i == self.selected_index else COLOR_TEXT
            prefix = "> " if i == self.selected_index else ""
            text_surf = self.font_menu.render(f"{prefix}{option}", True, color)
            text_rect = text_surf.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + i * 60))
            surface.blit(text_surf, text_rect)
