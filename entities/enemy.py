import pygame
from entities.entity import Entity
from combat.hitbox import AttackBox
from settings import *
from rendering.sprite_renderer import SpriteRenderer
import random
import os


class DummyEnemy(Entity):
    """
    Basic enemy type used for spawning during Phase 1.
    Behaviour is driven externally by EnemyAI.
    Has contact damage via always-active attack_box.
    """

    def __init__(self, x: float, y: float):
        super().__init__(x, y, TILE_SIZE * 0.75, TILE_SIZE * 0.75, COLOR_ENEMY)

        self.max_health = 60.0
        self.health = self.max_health
        self.speed = 120.0
        self.hurtbox.default_iframes = 0.15

        # Contact damage — always active so enemy damages on touch
        self.attack_box = AttackBox(
            self.width * 0.9, self.height * 0.9,
            damage=8, knockback=4.0
        )
        self.attack_box.active = True   # contact-damage style

        # Flash colour when hit
        self._flash_timer: float = 0.0
        self._base_color = COLOR_ENEMY

        # Sprite setup
        self.sprite_renderer = SpriteRenderer()
        enemy_files = [
            "alien.png", "crystal monster.png", "parasite.png", 
            "robot.png", "shadow.png", "slime.png", 
            "void creature.png", "worm.png"
        ]
        chosen = random.choice(enemy_files)
        self.sprite_renderer.load_sprite("enemy", f"enemies/{chosen}")

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        super().update(dt)
        
        # Clear hit set for contact damage to allow re-hitting after iframes expire
        self.attack_box.hit_set.clear()

        # Flash red-white briefly on damage (set by take_damage override)
        if self._flash_timer > 0:
            self._flash_timer -= dt
            if self._flash_timer <= 0:
                self.color = self._base_color

        # Keep attack box always synced
        self.attack_box.update(self.x, self.y)

    def take_damage(self, amount: float, source) -> None:
        super().take_damage(amount, source)
        # Hit flash
        self._flash_timer = 0.12
        self.color = (255, 255, 255)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(self, surface: pygame.Surface,
               offset_x: int = 0, offset_y: int = 0) -> None:
        if self.hurtbox and self.hurtbox.should_blink():
            return

        flip_x = self.velocity_x < 0
        tint = (255, 100, 100) if self._flash_timer > 0 else None
        
        self.sprite_renderer.render_sprite(
            surface, "enemy", self.x, self.y, 
            offset_x, offset_y, scale=1.5, flip_x=flip_x, tint=tint
        )
