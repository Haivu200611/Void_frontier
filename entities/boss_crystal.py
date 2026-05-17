import pygame
import math
import random
from entities.boss import Boss
from settings import *

class CrystalTitan(Boss):
    def __init__(self, x: float, y: float):
        super().__init__(x, y, name="CRYSTAL TITAN", boss_type="boss_2_crystal_titan")
        self.max_health = 2000.0
        self.health = self.max_health
        self.color = (50, 200, 255)
        self._base_color = self.color
        self.state = "idle"
        self.state_timer = 2.5
        
        self.reward = "artifact_1"

    def render(self, surface: pygame.Surface, offset_x: int = 0, offset_y: int = 0) -> None:
        if self.hurtbox and self.hurtbox.should_blink():
            return
            
        flip_x = self.velocity_x < 0
        tint = (200, 255, 255) if self.phase == 2 else None
        if self._flash_timer > 0:
            tint = (255, 150, 150)
            
        sprite = "boss"
        if hasattr(self, 'animation_player') and self.animation_player and self.animation_player.get_current_sprite():
            sprite = self.animation_player.get_current_sprite()

        self.sprite_renderer.render_sprite_to_size(
            surface, sprite, self.x, self.y,
            self.width, self.height,
            offset_x, offset_y, flip_x=flip_x, tint=tint
        )

    def update(self, dt: float, player=None, projectile_pool=None) -> None:
        super().update(dt, player, projectile_pool)
        
        self.state_timer -= dt
        
        # Phase 2 transition
        if self.health < self.max_health * 0.5 and self.phase == 1:
            self.phase = 2
            self.color = (200, 255, 255)
            self.speed = 60.0
            self.max_health = 3000.0 # Buff health for phase 2
            self.health = self.max_health * 0.5 # Keep current health
        
        if self.state == "idle":
            self.speed = 45.0 if self.phase == 1 else 70.0
            if player:
                dx = player.x - self.x
                dy = player.y - self.y
                dist = math.hypot(dx, dy)
                if dist > 150:
                    self.x += (dx / dist) * self.speed * dt
                    self.y += (dy / dist) * self.speed * dt
            
            if self.state_timer <= 0:
                self._choose_next_attack(player)
                
        elif self.state == "spikes":
            self.speed = 0.0
            if self.state_timer <= 0:
                if projectile_pool:
                    count = 12 if self.phase == 1 else 16
                    for i in range(count):
                        angle = (i / count) * math.tau
                        projectile_pool.spawn(self.x, self.y, 
                                            math.cos(angle), math.sin(angle), 
                                            250, 3.0, 20, 
                                            (100, 230, 255), 10, "enemy")
                self.state = "idle"
                self.state_timer = 1.5
                
        elif self.state == "reflection":
            self.speed = 20.0
            if self.state_timer <= 0:
                if projectile_pool and player:
                    # Burst of reflecting shards
                    count = 5 if self.phase == 1 else 8
                    for i in range(count):
                        angle = math.atan2(player.y - self.y, player.x - self.x) + random.uniform(-0.4, 0.4)
                        projectile_pool.spawn(self.x, self.y, 
                                            math.cos(angle), math.sin(angle), 
                                            500, 2.5, 12, 
                                            (0, 150, 255), 7, "enemy")
                self.state = "idle"
                self.state_timer = 2.0
                
        elif self.state == "barrage":
            # Fire rapid small shards
            chance = 0.3 if self.phase == 1 else 0.5
            if random.random() < chance and projectile_pool:
                angle = random.uniform(0, math.tau)
                projectile_pool.spawn(self.x, self.y, 
                                    math.cos(angle), math.sin(angle), 
                                    400, 1.5, 8, 
                                    (180, 240, 255), 5, "enemy")
            if self.state_timer <= 0:
                self.state = "idle"
                self.state_timer = 1.0

    def _choose_next_attack(self, player):
        attacks = ["spikes", "reflection", "barrage"]
        self.state = random.choice(attacks)
        
        if self.state == "spikes":
            self.state_timer = 1.0
        elif self.state == "reflection":
            self.state_timer = 1.2
        elif self.state == "barrage":
            self.state_timer = 3.0
