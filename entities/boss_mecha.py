import pygame
import math
import random
from entities.boss import Boss
from rendering.sprite_renderer import SpriteRenderer
from settings import *

class MechaBeast(Boss):
    def __init__(self, x: float, y: float):
        super().__init__(x, y, name="MECHA BEAST")
        self.sprite_renderer = SpriteRenderer()
        self.sprite_renderer.load_sprite("boss", "bosses/boss_1_mecha_beast.png")
        self.max_health = 1500.0
        self.health = self.max_health
        self.color = (180, 50, 50)
        self._base_color = self.color
        self.state = "idle"
        self.state_timer = 2.0
        
        self.reward = "battery_core"
        self.charge_dir = (0, 0)

    def update(self, dt: float, player=None, projectile_pool=None) -> None:
        super().update(dt, player, projectile_pool)
        
        self.state_timer -= dt
        
        # Phase 2 transition
        if self.health < self.max_health * 0.5 and self.phase == 1:
            self.phase = 2
            self.color = (255, 100, 0)
            self.speed = 110.0
            self.max_health = 2000.0 # Buff health for phase 2
            self.health = self.max_health * 0.5 # Keep current health
        
        if self.state == "idle":
            self.speed = 85.0 if self.phase == 1 else 130.0
            if player:
                dx = player.x - self.x
                dy = player.y - self.y
                dist = math.hypot(dx, dy)
                if dist > 120:
                    self.x += (dx / dist) * self.speed * dt
                    self.y += (dy / dist) * self.speed * dt
            
            if self.state_timer <= 0:
                self._choose_next_attack(player)
                
        elif self.state == "charge":
            self.speed = 450.0 if self.state_timer < 2.0 else 0.0 # windup then rush
            if self.state_timer > 0:
                self.x += self.charge_dir[0] * self.speed * dt
                self.y += self.charge_dir[1] * self.speed * dt
            else:
                self.state = "idle"
                self.state_timer = 1.5
                
        elif self.state == "slam":
            self.speed = 0.0
            if self.state_timer <= 0:
                # Spawn shockwave projectiles
                if projectile_pool:
                    count = 8 if self.phase == 1 else 12
                    for i in range(count):
                        angle = (i / count) * math.tau
                        projectile_pool.spawn(self.x, self.y, 
                                            math.cos(angle), math.sin(angle), 
                                            300, 1.5, 15, 
                                            (255, 100, 50), 8, "enemy")
                self.state = "idle"
                self.state_timer = 1.0
                
        elif self.state == "laser":
            self.speed = 30.0
            # Continuous laser sweep logic could go here, but for now just a burst
            if self.state_timer <= 0:
                if projectile_pool and player:
                    dx = player.x - self.x
                    dy = player.y - self.y
                    base_angle = math.atan2(dy, dx)
                    offsets = [-0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3] if self.phase == 2 else [-0.2, -0.1, 0, 0.1, 0.2]
                    for offset in offsets:
                        angle = base_angle + offset
                        projectile_pool.spawn(self.x, self.y, 
                                            math.cos(angle), math.sin(angle), 
                                            450, 2.0, 10, 
                                            (255, 50, 50), 6, "enemy")
                self.state = "idle"
                self.state_timer = 2.0

    def _choose_next_attack(self, player):
        attacks = ["charge", "slam", "laser"]
        self.state = random.choice(attacks)
        
        if self.state == "charge" and player:
            dx = player.x - self.x
            dy = player.y - self.y
            dist = math.hypot(dx, dy)
            if dist > 0:
                self.charge_dir = (dx/dist, dy/dist)
            self.state_timer = 3.0 # 1s windup + 2s charge
        elif self.state == "slam":
            self.state_timer = 0.8
        elif self.state == "laser":
            self.state_timer = 1.2

    def render(self, surface: pygame.Surface, offset_x: int = 0, offset_y: int = 0) -> None:
        if self.hurtbox and self.hurtbox.should_blink():
            return
            
        # Tint boss based on phase
        tint = (255, 100, 100) if self.phase == 2 else None
        self.sprite_renderer.render_sprite_to_size(
            surface, "boss", self.x, self.y,
            self.width, self.height,
            offset_x, offset_y, tint=tint
        )
