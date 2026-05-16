import math
import random

import pygame

from core.state_machine import State
from settings import *
from systems.localization import get_localization_manager, _ as tr


class MenuState(State):
    def enter(self, **kwargs):
        self.font_title = pygame.font.SysFont("impact", 108)
        self.font_subtitle = pygame.font.SysFont("segoeui", 24)
        self.font_menu = pygame.font.SysFont("segoeui", 34)
        self.font_hint = pygame.font.SysFont("segoeui", 20)
        self.font_language = pygame.font.SysFont("segoeui", 18)
        
        self.loc_manager = get_localization_manager()
        self.options = [
            tr("menu.play"),
            tr("menu.how_to_play"),
            tr("menu.language"),
            tr("menu.quit"),
        ]
        self.selected_index = 0
        self._mouse_pressed_last = False
        self.time = 0.0

        self.stars = []
        for i in range(160):
            self.stars.append(
                {
                    "x": random.uniform(0, WINDOW_WIDTH),
                    "y": random.uniform(0, WINDOW_HEIGHT),
                    "size": random.uniform(1.0, 2.8),
                    "speed": random.uniform(6.0, 24.0),
                    "phase": random.uniform(0, math.tau),
                }
            )

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w):
                    self.selected_index = (self.selected_index - 1) % len(self.options)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.selected_index = (self.selected_index + 1) % len(self.options)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.select_option()

            elif event.type == pygame.MOUSEMOTION:
                idx = self._option_from_mouse(event.pos)
                if idx is not None:
                    self.selected_index = idx

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                idx = self._option_from_mouse(event.pos)
                if idx is not None:
                    self.selected_index = idx
                    self.select_option()

    def select_option(self):
        option_index = self.selected_index
        if option_index == 0:  # Play
            self.engine.state_machine.change_state("Play")
        elif option_index == 1:  # How to Play
            self.engine.state_machine.change_state("HowToPlay")
        elif option_index == 2:  # Language
            self.engine.state_machine.change_state("LanguageMenu")
        elif option_index == 3:  # Quit
            self.engine.running = False

    def update(self, dt):
        self.time += dt
        for star in self.stars:
            star["y"] += star["speed"] * dt
            if star["y"] > WINDOW_HEIGHT + 4:
                star["y"] = -4
                star["x"] = random.uniform(0, WINDOW_WIDTH)

    def _option_rect(self, index: int) -> pygame.Rect:
        width = 360
        height = 56
        x = WINDOW_WIDTH // 2 - width // 2
        y = WINDOW_HEIGHT // 2 + 20 + index * 72
        return pygame.Rect(x, y, width, height)

    def _option_from_mouse(self, pos):
        for i in range(len(self.options)):
            if self._option_rect(i).collidepoint(pos):
                return i
        return None

    def _render_galaxy_background(self, surface):
        # Deep-space gradient
        for y in range(WINDOW_HEIGHT):
            t = y / max(1, WINDOW_HEIGHT - 1)
            r = int(10 + 20 * t)
            g = int(8 + 14 * t)
            b = int(28 + 45 * t)
            pygame.draw.line(surface, (r, g, b), (0, y), (WINDOW_WIDTH, y))

        # Nebula blobs
        nebula = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(nebula, (70, 55, 130, 78), (int(WINDOW_WIDTH * 0.22), int(WINDOW_HEIGHT * 0.28)), 240)
        pygame.draw.circle(nebula, (45, 95, 165, 70), (int(WINDOW_WIDTH * 0.75), int(WINDOW_HEIGHT * 0.34)), 260)
        pygame.draw.circle(nebula, (120, 70, 120, 52), (int(WINDOW_WIDTH * 0.50), int(WINDOW_HEIGHT * 0.67)), 300)
        surface.blit(nebula, (0, 0))

        # Stars
        for star in self.stars:
            twinkle = 0.6 + 0.4 * math.sin(self.time * 2.3 + star["phase"])
            alpha = int(140 + 110 * twinkle)
            size = max(1, int(star["size"]))
            s = pygame.Surface((size * 2 + 2, size * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (220, 235, 255, alpha), (size + 1, size + 1), size)
            surface.blit(s, (int(star["x"]), int(star["y"])))

        # Planet silhouette
        planet = pygame.Surface((360, 360), pygame.SRCALPHA)
        pygame.draw.circle(planet, (20, 36, 70, 210), (180, 180), 150)
        pygame.draw.circle(planet, (56, 85, 145, 90), (130, 120), 60)
        pygame.draw.circle(planet, (82, 138, 200, 65), (220, 220), 74)
        surface.blit(planet, (WINDOW_WIDTH - 340, -110))

    def render(self, surface):
        self._render_galaxy_background(surface)

        title_surf = self.font_title.render("VOID FRONTIER", True, (190, 235, 255))
        title_shadow = self.font_title.render("VOID FRONTIER", True, (35, 60, 95))
        title_rect = title_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 4 - 10))
        surface.blit(title_shadow, (title_rect.x + 3, title_rect.y + 4))
        surface.blit(title_surf, title_rect)

        subtitle = self.font_subtitle.render("SURVIVE THE EDGE OF THE GALAXY", True, (180, 200, 235))
        subtitle_rect = subtitle.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 4 + 56))
        surface.blit(subtitle, subtitle_rect)

        for i, option in enumerate(self.options):
            rect = self._option_rect(i)
            selected = i == self.selected_index

            bg = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            if selected:
                bg.fill((90, 160, 230, 120))
                border = (185, 230, 255)
                txt_color = (245, 252, 255)
            else:
                bg.fill((20, 34, 56, 150))
                border = (95, 130, 170)
                txt_color = (200, 220, 245)

            surface.blit(bg, rect.topleft)
            pygame.draw.rect(surface, border, rect, 2, border_radius=8)

            text = self.font_menu.render(option, True, txt_color)
            text_rect = text.get_rect(center=rect.center)
            surface.blit(text, text_rect)

        hint_text = "W/S or Arrow Keys + Enter   |   Mouse Click"
        if self.loc_manager.get_language() == "vi":
            hint_text = "W/S hoặc Mũi Tên + Enter   |   Nhấp Chuột"
        hint = self.font_hint.render(hint_text, True, (140, 170, 205))
        hint_rect = hint.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 36))
        surface.blit(hint, hint_rect)
        
        # Display current language
        lang_code = self.loc_manager.get_language()
        lang_name = self.loc_manager.get_language_name(lang_code)
        lang_label = "Language" if lang_code == "en" else "Ngôn ngữ"
        lang_text = self.font_language.render(f"{lang_label}: {lang_name}", True, (150, 150, 150))
        surface.blit(lang_text, (WINDOW_WIDTH - 220, 20))
