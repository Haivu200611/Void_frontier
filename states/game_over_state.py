import math
import random

import pygame

from core.state_machine import State
from settings import *


class GameOverState(State):
    def enter(self, **kwargs):
        self.font_title = pygame.font.SysFont("impact", 96)
        self.font_text = pygame.font.SysFont("arial", 30)
        self.font_hint = pygame.font.SysFont("arial", 22)
        self.timer = 0.0

        self.reason = kwargs.get("reason", "You were overwhelmed in the Void Frontier.")
        self.world_name = kwargs.get("world", "unknown")

        self.options = ["RETRY", "MAIN MENU"]
        self.selected_index = 0

        self.particles = []
        for _ in range(100):
            self.particles.append(
                {
                    "x": random.uniform(0, WINDOW_WIDTH),
                    "y": random.uniform(0, WINDOW_HEIGHT),
                    "vx": random.uniform(-12, 12),
                    "vy": random.uniform(-30, -8),
                    "size": random.uniform(1.2, 3.0),
                    "phase": random.uniform(0, math.tau),
                }
            )

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w, pygame.K_LEFT, pygame.K_a):
                    self.selected_index = (self.selected_index - 1) % len(self.options)
                elif event.key in (pygame.K_DOWN, pygame.K_s, pygame.K_RIGHT, pygame.K_d):
                    self.selected_index = (self.selected_index + 1) % len(self.options)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._confirm()
            elif event.type == pygame.MOUSEMOTION:
                idx = self._option_from_mouse(event.pos)
                if idx is not None:
                    self.selected_index = idx
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                idx = self._option_from_mouse(event.pos)
                if idx is not None:
                    self.selected_index = idx
                    self._confirm()

    def _confirm(self):
        option = self.options[self.selected_index]
        if option == "RETRY":
            self.engine.state_machine.change_state("Play")
        else:
            self.engine.state_machine.change_state("Menu")

    def update(self, dt):
        self.timer += dt
        for p in self.particles:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            if p["y"] < -10:
                p["y"] = WINDOW_HEIGHT + 10
                p["x"] = random.uniform(0, WINDOW_WIDTH)
            if p["x"] < -10:
                p["x"] = WINDOW_WIDTH + 10
            elif p["x"] > WINDOW_WIDTH + 10:
                p["x"] = -10

    def _option_rect(self, index: int) -> pygame.Rect:
        w, h = 280, 54
        total_w = len(self.options) * w + (len(self.options) - 1) * 24
        start_x = WINDOW_WIDTH // 2 - total_w // 2
        x = start_x + index * (w + 24)
        y = WINDOW_HEIGHT // 2 + 120
        return pygame.Rect(x, y, w, h)

    def _option_from_mouse(self, pos):
        for i in range(len(self.options)):
            if self._option_rect(i).collidepoint(pos):
                return i
        return None

    def render(self, surface):
        # Dark red-space gradient
        for y in range(WINDOW_HEIGHT):
            t = y / max(1, WINDOW_HEIGHT - 1)
            r = int(18 + 40 * t)
            g = int(8 + 12 * t)
            b = int(12 + 18 * t)
            pygame.draw.line(surface, (r, g, b), (0, y), (WINDOW_WIDTH, y))

        # Vignette-like overlay
        shade = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 90))
        surface.blit(shade, (0, 0))

        # Floating embers
        for p in self.particles:
            glow = 0.5 + 0.5 * math.sin(self.timer * 2.0 + p["phase"])
            col = (255, 90, 90, int(120 * glow))
            s = max(1, int(p["size"]))
            dot = pygame.Surface((s * 2 + 2, s * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(dot, col, (s + 1, s + 1), s)
            surface.blit(dot, (int(p["x"]), int(p["y"])))

        # Main panel
        panel = pygame.Surface((920, 380), pygame.SRCALPHA)
        panel.fill((14, 10, 16, 190))
        px, py = WINDOW_WIDTH // 2 - 460, WINDOW_HEIGHT // 2 - 210
        surface.blit(panel, (px, py))
        pygame.draw.rect(surface, (180, 80, 95), (px, py, 920, 380), 2, border_radius=8)

        title_shadow = self.font_title.render("GAME OVER", True, (55, 16, 24))
        title = self.font_title.render("GAME OVER", True, (255, 120, 135))
        tx = WINDOW_WIDTH // 2 - title.get_width() // 2
        ty = WINDOW_HEIGHT // 2 - 155
        surface.blit(title_shadow, (tx + 3, ty + 4))
        surface.blit(title, (tx, ty))

        world_text = self.font_text.render(f"World: {self.world_name}", True, (215, 190, 200))
        world_rect = world_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 20))
        surface.blit(world_text, world_rect)

        reason_text = self.font_hint.render(self.reason, True, (235, 205, 215))
        reason_rect = reason_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 20))
        surface.blit(reason_text, reason_rect)

        for i, opt in enumerate(self.options):
            rect = self._option_rect(i)
            selected = i == self.selected_index

            bg = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            if selected:
                bg.fill((190, 70, 85, 160))
                border = (255, 170, 180)
                txt = (255, 240, 242)
            else:
                bg.fill((52, 28, 38, 140))
                border = (145, 92, 106)
                txt = (225, 200, 210)

            surface.blit(bg, rect.topleft)
            pygame.draw.rect(surface, border, rect, 2, border_radius=8)
            t = self.font_text.render(opt, True, txt)
            tr = t.get_rect(center=rect.center)
            surface.blit(t, tr)
