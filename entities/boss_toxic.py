import pygame
import math
import random
from entities.boss import Boss
from settings import *

class ToxicWorm(Boss):
    def __init__(self, x: float, y: float):
        super().__init__(x, y, name="TOXIC WORM", boss_type="boss_3_toxic_worm")
        self.max_health = 2500.0
        self.health = self.max_health
        self.color = (50, 255, 50)
        self._base_color = self.color
        self.state = "idle"
        self.state_timer = 2.0
        
        self.reward = "artifact_2"

    def render(self, surface: pygame.Surface, offset_x: int = 0, offset_y: int = 0) -> None:
        if self.hurtbox and self.hurtbox.should_blink():
            return
            
        flip_x = self.velocity_x < 0
        alpha = 100 if self.state == "burrow" else 255
        tint = (150, 255, 150) if self.phase == 2 else None
        if self._flash_timer > 0:
            tint = (255, 150, 150)
            
        sprite = "boss"
        if hasattr(self, 'animation_player') and self.animation_player and self.animation_player.get_current_sprite():
            sprite = self.animation_player.get_current_sprite()
            
        self.sprite_renderer.render_sprite_to_size(
            surface, sprite, self.x, self.y,
            self.width, self.height,
            offset_x, offset_y, flip_x=flip_x, tint=tint, alpha=alpha
        )

    def update(self, dt: float, player=None, projectile_pool=None) -> None:
        super().update(dt, player, projectile_pool)
        
        self.state_timer -= dt
        
        # Phase 2 transition
        if self.health < self.max_health * 0.5 and self.phase == 1:
            self.phase = 2
            self.color = (150, 255, 150)
            self.speed = 130.0
            self.max_health = 3500.0 # Buff health for phase 2
            self.health = self.max_health * 0.5 # Keep current health
        
        if self.state == "idle":
            self.speed = 100.0 if self.phase == 1 else 130.0
            if player:
                dx = player.x - self.x
                dy = player.y - self.y
                dist = math.hypot(dx, dy)
                if dist > 100:
                    self.x += (dx / dist) * self.speed * dt
                    self.y += (dy / dist) * self.speed * dt
            
            if self.state_timer <= 0:
                self._choose_next_attack(player)
                
        elif self.state == "burrow":
            self.speed = 180.0 if self.phase == 1 else 240.0
            self.hurtbox.active = False # Invulnerable
            self.color = (30, 100, 30)
            
            if player:
                dx = player.x - self.x
                dy = player.y - self.y
                dist = math.hypot(dx, dy)
                if dist > 10:
                    self.x += (dx/dist) * self.speed * dt
                    self.y += (dy/dist) * self.speed * dt
            
            if self.state_timer <= 0:
                self.state = "ambush"
                self.state_timer = 0.5 # pop up delay
                
        elif self.state == "ambush":
            self.speed = 0.0
            self.hurtbox.active = True
            self.color = (255, 255, 100) # Warning color
            if self.state_timer <= 0:
                # Burst on pop up
                if projectile_pool:
                    count = 16 if self.phase == 1 else 24
                    for i in range(count):
                        angle = (i / count) * math.tau
                        projectile_pool.spawn(self.x, self.y, 
                                            math.cos(angle), math.sin(angle), 
                                            350, 1.0, 25, 
                                            (150, 255, 100), 12, "enemy")
                self.state = "idle"
                self.state_timer = 1.5
                self.color = self._base_color
                
        elif self.state == "spit":
            self.speed = 40.0
            if self.state_timer <= 0:
                if projectile_pool and player:
                    dx = player.x - self.x
                    dy = player.y - self.y
                    dist = math.hypot(dx, dy)
                    if dist > 0:
                        # Spit multiple projectiles that slow down and stay
                        count = 3 if self.phase == 1 else 5
                        for i in range(count):
                            angle = math.atan2(dy, dx) + random.uniform(-0.3, 0.3)
                            projectile_pool.spawn(self.x, self.y, 
                                                math.cos(angle), math.sin(angle), 
                                                400, 5.0, 15, 
                                                (50, 200, 50), 15, "enemy")
                self.state = "idle"
                self.state_timer = 2.0

    def _choose_next_attack(self, player):
        attacks = ["burrow", "spit"]
        self.state = random.choice(attacks)
        
        if self.state == "burrow":
            self.state_timer = 3.0
        elif self.state == "spit":
            self.state_timer = 0.8
