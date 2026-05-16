"""
Language Selection Menu State
"""
import os

import pygame

from core.state_machine import State
from settings import *
from ui.background import SpaceBackground
from systems.localization import get_localization_manager


class LanguageMenuState(State):
    """Language selection menu"""

    def enter(self, **kwargs):
        self.font_title = pygame.font.SysFont("segoeui", 56, bold=True)
        self.font_button = pygame.font.SysFont("segoeui", 32, bold=True)
        self.font_info = pygame.font.SysFont("segoeui", 20)
        self.background = SpaceBackground()

        self.loc_manager = get_localization_manager()
        self.languages = self.loc_manager.available_languages
        self.selected_index = 0
        self.buttons = []
        self.create_buttons()

    def create_buttons(self):
        """Create language selection buttons"""
        self.buttons = []
        button_width = 300
        button_height = 80
        spacing = 120

        total_width = len(self.languages) * (button_width + spacing) - spacing
        start_x = (WINDOW_WIDTH - total_width) // 2

        for i, lang_code in enumerate(self.languages):
            x = start_x + i * (button_width + spacing)
            y = WINDOW_HEIGHT // 2 - 100

            lang_name = self.loc_manager.get_language_name(lang_code)
            self.buttons.append(
                {
                    "rect": pygame.Rect(x, y, button_width, button_height),
                    "code": lang_code,
                    "name": lang_name,
                }
            )

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.engine.state_machine.change_state("Menu")
                elif event.key == pygame.K_LEFT:
                    self.selected_index = (self.selected_index - 1) % len(self.buttons)
                elif event.key == pygame.K_RIGHT:
                    self.selected_index = (self.selected_index + 1) % len(self.buttons)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    self.select_language(self.selected_index)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    mouse_pos = event.pos
                    for i, btn in enumerate(self.buttons):
                        if btn["rect"].collidepoint(mouse_pos):
                            self.selected_index = i
                            self.select_language(i)
                            break
            elif event.type == pygame.MOUSEMOTION:
                mouse_pos = event.pos
                for i, btn in enumerate(self.buttons):
                    if btn["rect"].collidepoint(mouse_pos):
                        self.selected_index = i
                        break

    def select_language(self, index: int):
        """Select and save language"""
        if 0 <= index < len(self.buttons):
            lang_code = self.buttons[index]["code"]
            self.loc_manager.set_language(lang_code)
            self.save_language_preference(lang_code)
            self.engine.state_machine.change_state("Menu")

    def save_language_preference(self, lang_code: str):
        """Save language preference to file"""
        try:
            pref_file = os.path.join(".", "language_preference.txt")
            with open(pref_file, "w", encoding="utf-8") as f:
                f.write(lang_code)
        except Exception as e:
            print(f"Error saving language preference: {e}")

    def update(self, dt):
        self.background.update(dt)

    def render(self, surface):
        self.background.render(surface)

        # Draw main panel
        panel = pygame.Surface((WINDOW_WIDTH - 80, WINDOW_HEIGHT - 100), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 220))
        pygame.draw.rect(surface, (100, 200, 255), (40, 40, WINDOW_WIDTH - 80, WINDOW_HEIGHT - 100), 3)
        surface.blit(panel, (40, 40))

        # Draw title
        title_text = "SELECT LANGUAGE / CHỌN NGÔN NGỮ"
        title_surf = self.font_title.render(title_text, True, (100, 200, 255))
        title_rect = title_surf.get_rect(center=(WINDOW_WIDTH // 2, 80))
        surface.blit(title_surf, title_rect)

        # Draw separator line
        pygame.draw.line(surface, (100, 200, 255), (60, 140), (WINDOW_WIDTH - 60, 140), 2)

        # Draw buttons
        for i, btn in enumerate(self.buttons):
            is_selected = i == self.selected_index

            # Button background
            button_color = (50, 220, 200) if is_selected else (20, 100, 120)
            pygame.draw.rect(surface, button_color, btn["rect"])
            pygame.draw.rect(surface, (100, 255, 255), btn["rect"], 3 if is_selected else 1)

            # Button text
            text_surf = self.font_button.render(btn["name"], True, (255, 255, 255))
            text_rect = text_surf.get_rect(center=btn["rect"].center)
            surface.blit(text_surf, text_rect)

        # Draw instructions
        info_text = "Press ARROW KEYS or CLICK to select | Press ENTER to confirm"
        info_surf = self.font_info.render(info_text, True, (150, 150, 150))
        info_rect = info_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 50))
        surface.blit(info_surf, info_rect)

        # Draw ESC hint
        esc_text = "Press ESC to go back"
        esc_surf = self.font_info.render(esc_text, True, (150, 100, 100))
        surface.blit(esc_surf, (40, WINDOW_HEIGHT - 30))
