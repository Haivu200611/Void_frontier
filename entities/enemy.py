import pygame
from entities.entity import Entity
from combat.hitbox import AttackBox
from settings import *
from rendering.sprite_renderer import SpriteRenderer
from rendering.animation_player import AnimationPlayer, Animation, Frame
import random
import os
import re


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
        self._hurt_anim_timer: float = 0.0
        self._hurt_anim_duration: float = 0.18
        self.death_remove_timer: float = 0.0

        # Sprite + animation setup
        self.sprite_renderer = SpriteRenderer()
        self.animation_player = AnimationPlayer()
        self.enemy_type = random.choice([
            "alien", "crystal monster", "parasite",
            "robot", "shadow", "slime",
            "void creature", "worm",
        ])
        self._load_enemy_animations()
        if "idle" in self.animation_player.animations:
            self.animation_player.play("idle")

        self.ai_state = None
        self.ai_state_name = "idle"

    _NUM_RE = re.compile(r"(\d+)")

    @classmethod
    def _sort_files_numeric(cls, files: list[str]) -> list[str]:
        def key_fn(name: str) -> int:
            m = cls._NUM_RE.search(name)
            return int(m.group(1)) if m else 0
        return sorted(files, key=key_fn)

    def _load_enemy_animations(self) -> None:
        """
        Load enemy animation set from:
        assets/images/enemies/<enemy_type>/{attack,death,hurt,idle,move}

        Note: `shadow` sprite pack uses `ilde` instead of `idle`.
        """
        base_dir = os.path.join("assets", "images", "enemies", self.enemy_type)
        action_dirs = {
            "attack": ["attack"],
            "death": ["death"],
            "hurt": ["hurt"],
            "idle": ["idle", "ilde"],
            "move": ["move"],
        }

        for action, candidates in action_dirs.items():
            action_dir = None
            for cand in candidates:
                candidate_dir = os.path.join(base_dir, cand)
                if os.path.isdir(candidate_dir):
                    action_dir = candidate_dir
                    break
            if action_dir is None:
                continue

            files = [
                f for f in os.listdir(action_dir)
                if os.path.isfile(os.path.join(action_dir, f))
                and f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
            ]
            files = self._sort_files_numeric(files)
            frames: list[Frame] = []

            for f in files:
                abs_path = os.path.abspath(os.path.join(action_dir, f))
                cache_key = f"enemy_{self.enemy_type}_{action}_{f}"
                surf = self.sprite_renderer.load_sprite(cache_key, abs_path)
                frames.append(Frame(surf, 1.0 / 24.0))

            if frames:
                loop = action != "death"
                self.animation_player.add_animation(Animation(action, frames, loop=loop))

        # Fallback static key if animation pack has issues
        idle_first = os.path.join(base_dir, "idle", "idle_01.png")
        if not os.path.exists(idle_first):
            idle_first = os.path.join(base_dir, "ilde", "idle_01.png")
        self.sprite_renderer.load_sprite("enemy", os.path.abspath(idle_first))

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
        if self._hurt_anim_timer > 0:
            self._hurt_anim_timer = max(0.0, self._hurt_anim_timer - dt)
        if self.is_dead and self.death_remove_timer > 0:
            self.death_remove_timer = max(0.0, self.death_remove_timer - dt)

        # Keep attack box always synced
        self.attack_box.update(self.x, self.y)

        self._update_animations(dt)

    def _update_animations(self, dt: float) -> None:
        # Animation state mapping for all enemies:
        # attack, death, hurt, idle, move.
        if self.animation_player:
            speed = (self.velocity_x * self.velocity_x + self.velocity_y * self.velocity_y) ** 0.5
            if self.is_dead and "death" in self.animation_player.animations:
                self.animation_player.play("death")
            elif self._hurt_anim_timer > 0 and "hurt" in self.animation_player.animations:
                self.animation_player.play("hurt")
            elif self.ai_state_name == "attack" and "attack" in self.animation_player.animations:
                self.animation_player.play("attack")
            elif speed > 0.1 and "move" in self.animation_player.animations:
                self.animation_player.play("move")
            elif "idle" in self.animation_player.animations:
                self.animation_player.play("idle")

            self.animation_player.update(dt)

    def take_damage(self, amount: float, source) -> None:
        old_health = self.health
        super().take_damage(amount, source)
        # Hit flash
        if self.health < old_health:
            self._flash_timer = 0.12
            self.color = (255, 255, 255)
            self._hurt_anim_timer = self._hurt_anim_duration
            if self.is_dead and self.death_remove_timer <= 0:
                death_anim = self.animation_player.animations.get("death") if self.animation_player else None
                self.death_remove_timer = max(0.35, death_anim.total_duration if death_anim else 0.35)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(self, surface: pygame.Surface,
               offset_x: int = 0, offset_y: int = 0) -> None:
        if self.hurtbox and self.hurtbox.should_blink():
            return

        flip_x = self.velocity_x < 0
        tint = (255, 100, 100) if self._flash_timer > 0 else None
        sprite = "enemy"
        if self.animation_player and self.animation_player.get_current_sprite():
            sprite = self.animation_player.get_current_sprite()

        self.sprite_renderer.render_sprite_to_size(
            surface, sprite, self.x, self.y,
            self.width, self.height,
            offset_x, offset_y, flip_x=flip_x, tint=tint
        )
