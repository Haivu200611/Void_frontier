import pygame
import random
from settings import *

class Star:
    def __init__(self):
        self.x = random.randint(0, WINDOW_WIDTH)
        self.y = random.randint(0, WINDOW_HEIGHT)
        self.speed = random.uniform(10, 30)
        self.size = random.randint(1, 3)
        self.color = (random.randint(150, 255), random.randint(150, 255), random.randint(150, 255))
        
    def update(self, dt):
        self.y += self.speed * dt
        if self.y > WINDOW_HEIGHT:
            self.y = 0
            self.x = random.randint(0, WINDOW_WIDTH)
            
    def render(self, surface):
        pygame.draw.rect(surface, self.color, (self.x, int(self.y), self.size, self.size))

class Meteor:
    def __init__(self):
        self.reset()
        self.y = random.randint(0, WINDOW_HEIGHT) # Initial random position
        
    def reset(self):
        self.x = random.randint(0, WINDOW_WIDTH)
        self.y = -50
        self.speed_x = random.uniform(-50, 50)
        self.speed_y = random.uniform(100, 300)
        self.size = random.randint(4, 8)
        self.color = (200, 150, 100)
        
    def update(self, dt):
        self.x += self.speed_x * dt
        self.y += self.speed_y * dt
        if self.y > WINDOW_HEIGHT + 50 or self.x < -50 or self.x > WINDOW_WIDTH + 50:
            self.reset()
            
    def render(self, surface):
        # Draw a trail
        end_x = self.x - self.speed_x * 0.1
        end_y = self.y - self.speed_y * 0.1
        pygame.draw.line(surface, self.color, (self.x, self.y), (end_x, end_y), 2)
        pygame.draw.rect(surface, (255, 200, 150), (int(self.x), int(self.y), self.size, self.size))

class SpaceBackground:
    def __init__(self):
        self.stars = [Star() for _ in range(100)]
        self.meteors = [Meteor() for _ in range(5)]
        
    def update(self, dt):
        for star in self.stars:
            star.update(dt)
        for meteor in self.meteors:
            meteor.update(dt)
            
    def render(self, surface):
        surface.fill(COLOR_BG)
        for star in self.stars:
            star.render(surface)
        for meteor in self.meteors:
            meteor.render(surface)
