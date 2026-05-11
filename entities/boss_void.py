import pygame
import math
import random
from entities.boss import Boss
from settings import *

class VoidGuardian(Boss):
    def __init__(self, x: float, y: float):
        super().__init__(x, y, name="VOID GUARDIAN")
        self.max_health = 4000.0
        self.health = self.max_health
        self.color = (150, 0, 255)
        self._base_color = self.color
        self.state = "idle"
        self.state_timer = 3.0
        
        self.reward = "artifact_3"

    def update(self, dt: float, player=None, projectile_pool=None) -> None:
        super().update(dt, player, projectile_pool)
        
        self.state_timer -= dt
        
        # Phase 2 transition
        if self.health < self.max_health * 0.5 and self.phase == 1:
            self.phase = 2
            self.color = (255, 0, 255)
            self.speed = 80.0
            self.max_health = 6000.0 # Buff health for phase 2
            self.health = self.max_health * 0.5 # Keep current health
        
        if self.state == "idle":
            self.speed = 65.0 if self.phase == 1 else 90.0
            if player:
                dx = player.x - self.x
                dy = player.y - self.y
                dist = math.hypot(dx, dy)
                if dist > 120:
                    self.x += (dx / dist) * self.speed * dt
                    self.y += (dy / dist) * self.speed * dt
            
            if self.state_timer <= 0:
                self._choose_next_attack(player)
                
        elif self.state == "teleport":
            self.speed = 0.0
            if self.state_timer <= 0 and player:
                # Teleport near player
                angle = random.uniform(0, math.tau)
                dist = random.uniform(200, 400)
                self.x = player.x + math.cos(angle) * dist
                self.y = player.y + math.sin(angle) * dist
                self.rect.center = (int(self.x), int(self.y))
                
                self.state = "idle"
                self.state_timer = 1.0
                
        elif self.state == "beam":
            self.speed = 10.0
            if player and projectile_pool:
                # Phase 2: More frequent and powerful beams
                chance = 0.2 if self.phase == 2 else 0.1
                if random.random() < chance:
                    dx = player.x - self.x
                    dy = player.y - self.y
                    angle = math.atan2(dy, dx)
                    projectile_pool.spawn(self.x, self.y, 
                                        math.cos(angle), math.sin(angle), 
                                        800, 1.0, 12, 
                                        (200, 0, 255), 4, "enemy")
            if self.state_timer <= 0:
                self.state = "idle"
                self.state_timer = 2.0
                
        elif self.state == "explosion":
            self.speed = 0.0
            if self.state_timer <= 0:
                if projectile_pool:
                    count = 32 if self.phase == 1 else 48
                    for i in range(count):
                        angle = (i / count) * math.tau
                        projectile_pool.spawn(self.x, self.y, 
                                            math.cos(angle), math.sin(angle), 
                                            150, 4.0, 30, 
                                            (100, 0, 200), 20, "enemy")
                self.state = "idle"
                self.state_timer = 2.5

    def _choose_next_attack(self, player):
        attacks = ["teleport", "beam", "explosion"]
        self.state = random.choice(attacks)
        
        if self.state == "teleport":
            self.state_timer = 0.5
        elif self.state == "beam":
            self.state_timer = 3.0
        elif self.state == "explosion":
            self.state_timer = 1.5
