from __future__ import annotations

import pygame

from entities.entity import Entity
from combat.hitbox import AttackBox
from rendering.sprite_renderer import SpriteRenderer
from systems.items import ItemDatabase
from settings import *


class Player(Entity):
    """
    Player entity.
    Handles movement and combat input while survival systems are managed in PlayState.
    """

    def __init__(self, x: float, y: float):
        super().__init__(x, y, TILE_SIZE * 0.75, TILE_SIZE * 0.75, COLOR_PLAYER)

        self.sprite_renderer = SpriteRenderer()
        self.sprite_renderer.load_sprite("player", "assets/images/player/idle.png")

        self.base_speed = 300.0
        self.speed = self.base_speed
        self.status_speed_multiplier = 1.0

        self.max_health = 100.0
        self.health = self.max_health
        self.hurtbox.default_iframes = 0.5

        self.max_oxygen = 100.0
        self.oxygen = self.max_oxygen
        self.max_hunger = 100.0
        self.hunger = self.max_hunger

        self.disable_survival_drain = False

        atk_size = TILE_SIZE * 1.4
        self.attack_box = AttackBox(atk_size, atk_size, damage=20, knockback=8.0)
        self.is_attacking = False
        self.attack_timer = 0.0
        self.attack_cooldown = 0.35

        self.shoot_timer = 0.0
        self.shoot_cooldown = 0.25

        self._camera = None
        self._camera_ref = None

        self.inventory = None

    def handle_input(self, dt: float, camera, projectile_pool) -> None:
        self._camera = camera
        self._camera_ref = camera
        keys = pygame.key.get_pressed()

        self.speed = self.base_speed * self.status_speed_multiplier

        self.velocity_x = 0.0
        self.velocity_y = 0.0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.velocity_y = -self.speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.velocity_y = self.speed
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.velocity_x = -self.speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.velocity_x = self.speed

        if self.velocity_x != 0 and self.velocity_y != 0:
            self.velocity_x *= 0.7071
            self.velocity_y *= 0.7071

        mouse_buttons = pygame.mouse.get_pressed()
        shift_down = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]

        if mouse_buttons[0] and not shift_down and not self.is_attacking and self.attack_timer <= 0:
            self._start_attack(camera)

        if mouse_buttons[2] and projectile_pool and self.shoot_timer <= 0:
            self._shoot(camera, projectile_pool)

    def _start_attack(self, camera) -> None:
        self.is_attacking = True
        self.attack_timer = self.attack_cooldown
        self.attack_box.activate()

        world_mx, world_my = self._mouse_world(camera)
        dx = world_mx - self.x
        dy = world_my - self.y
        dist = (dx * dx + dy * dy) ** 0.5
        if dist > 0:
            nx, ny = dx / dist, dy / dist
            reach = self.width * 0.5 + self.attack_box.rect.width * 0.5
            self.attack_box.offset_x = nx * reach
            self.attack_box.offset_y = ny * reach

    def _shoot(self, camera, projectile_pool) -> None:
        # Default kinetic stats (if no weapon equipped)
        dmg = 15
        spd = 640
        cool = 0.25
        life = 2.0
        clr = (0, 220, 255)
        
        # Check equipped weapon
        if self.inventory:
            weapon_stack = self.inventory.equipment.get("weapon")
            if weapon_stack:
                item = ItemDatabase.get_item(weapon_stack.item_id)
                if item and item.weapon_stats:
                    stats = item.weapon_stats
                    dmg = stats.get("damage", dmg)
                    spd = stats.get("speed", spd)
                    cool = stats.get("cooldown", cool)
                    life = stats.get("lifetime", life)
                    clr = tuple(stats.get("color", clr))

        self.shoot_timer = cool
        world_mx, world_my = self._mouse_world(camera)
        dx = world_mx - self.x
        dy = world_my - self.y
        
        projectile_pool.spawn(
            self.x,
            self.y,
            dx,
            dy,
            speed=spd,
            lifetime=life,
            damage=dmg,
            color=clr,
            radius=4,
            owner_layer="player",
        )

    @staticmethod
    def _mouse_world(camera) -> tuple[float, float]:
        mx, my = pygame.mouse.get_pos()
        offset = camera.get_offset()
        return (mx + offset.x, my + offset.y)

    def handle_combat_timers(self, dt: float) -> None:
        if self.shoot_timer > 0:
            self.shoot_timer -= dt

        if self.attack_timer > 0:
            self.attack_timer -= dt
            if self.attack_timer <= 0:
                self.is_attacking = False
                self.attack_box.deactivate()

    def handle_survival(self, dt: float) -> None:
        if not self.disable_survival_drain:
            self.oxygen = max(0.0, self.oxygen - 0.8 * dt)
            self.hunger = max(0.0, self.hunger - 0.4 * dt)

        if self.oxygen <= 0:
            self.health -= 5.0 * dt

    def update(self, dt: float, camera, projectile_pool=None) -> None:
        self.handle_input(dt, camera, projectile_pool)
        self.handle_combat_timers(dt)
        super().update(dt)
        self.handle_survival(dt)

    def render(self, surface: pygame.Surface, offset_x: int = 0, offset_y: int = 0) -> None:
        if self.hurtbox and self.hurtbox.should_blink():
            return

        flip_x = self.velocity_x < 0
        self.sprite_renderer.render_sprite(surface, "player", self.x, self.y, offset_x, offset_y, 
                                         scale=1.5, flip_x=flip_x)

        render_rect = self.rect.move(-offset_x, -offset_y)
        if self._camera:
            world_mx, world_my = self._mouse_world(self._camera)
            dx = world_mx - self.x
            dy = world_my - self.y
            dist = (dx * dx + dy * dy) ** 0.5
            if dist > 0:
                nx, ny = dx / dist, dy / dist
                tip_x = render_rect.centerx + int(nx * self.width * 0.65)
                tip_y = render_rect.centery + int(ny * self.height * 0.65)
                pygame.draw.circle(surface, (255, 255, 100), (tip_x, tip_y), 4)

    def render_debug(self, surface: pygame.Surface, offset_x: int = 0, offset_y: int = 0) -> None:
        super().render_debug(surface, offset_x, offset_y)
        if self.shoot_timer > 0:
            bar_x = self.rect.x - offset_x
            bar_y = self.rect.y - offset_y - 16
            ratio = self.shoot_timer / self.shoot_cooldown
            pygame.draw.rect(surface, (0, 80, 180), (bar_x, bar_y, int(self.width), 4))
            pygame.draw.rect(surface, (0, 180, 255), (bar_x, bar_y, int(self.width * (1 - ratio)), 4))
