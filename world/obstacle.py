import pygame
from settings import *

class Obstacle:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        
    def render(self, surface, offset_x=0, offset_y=0):
        render_rect = self.rect.copy()
        render_rect.x -= offset_x
        render_rect.y -= offset_y
        pygame.draw.rect(surface, COLOR_ORE, render_rect)
