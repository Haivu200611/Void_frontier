import pygame
import os
from core.state_machine import State
from settings import *

class EndingState(State):
    def enter(self, **kwargs):
        # Read language preference
        self.lang = "en"
        lang_path = "language_preference.txt"
        if os.path.exists(lang_path):
            with open(lang_path, "r", encoding="utf-8") as f:
                self.lang = f.read().strip()
                
        # Setup fonts (use segoeui or arial for Vietnamese support)
        self.font = pygame.font.SysFont("segoeui", 48)
        self.sub_font = pygame.font.SysFont("segoeui", 28)
        self.timer = 0.0
        
        # Determine text
        if self.lang == "vi":
            self.title_text = "NHIỆM VỤ HOÀN THÀNH"
            self.desc_text = "bạn đã thoát khỏi void frontier hãy tiếp tục chuyến hành trình của bạn và đừng quay đầu"
            self.prompt_text = "Nhấn Enter để quay về Menu"
        else:
            self.title_text = "MISSION ACCOMPLISHED"
            self.desc_text = "You have escaped the void frontier, continue your journey and don't look back"
            self.prompt_text = "Press Enter to return to main menu"
            
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.engine.state_machine.change_state("Menu")
                    
    def update(self, dt):
        self.timer += dt
        
    def render(self, surface):
        surface.fill((10, 10, 20))
        
        # Center text
        title = self.font.render(self.title_text, True, (200, 255, 200))
        title_rect = title.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 50))
        surface.blit(title, title_rect)
        
        desc = self.sub_font.render(self.desc_text, True, (150, 200, 150))
        desc_rect = desc.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 20))
        surface.blit(desc, desc_rect)
        
        if self.timer % 1.5 > 0.5: # Blinking prompt
            prompt = self.sub_font.render(self.prompt_text, True, (100, 100, 100))
            prompt_rect = prompt.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 100))
            surface.blit(prompt, prompt_rect)
