import pygame
from entities.enemy import DummyEnemy
from combat.hitbox import AttackBox
from settings import *


class Boss(DummyEnemy):
    """
    Boss entity — larger, tougher, multi-phase.
    Inherits from DummyEnemy; driven by EnemyAI with an aggro_radius override.
    """

    def __init__(self, x: float, y: float, name: str = "MECHA BEAST", boss_type: str = "boss_1_mecha_beast"):
        self.boss_type = boss_type
        super().__init__(x, y)

        self.name = name
        self.phase = 1
        self.state = "IDLE" # IDLE, INTRO, CHASE, ATTACK, SPECIAL, STUNNED, RAGE, DEATH

        # Override size and stats
        self.width  = TILE_SIZE * 2.5
        self.height = TILE_SIZE * 2.5
        self.max_health = 1000.0
        self.health = self.max_health
        self.speed = 70.0
        self.color = COLOR_BOSS
        self._base_color = COLOR_BOSS
        self.hurtbox.default_iframes = 0.05

        # Rebuild rects for new size
        self.rect = pygame.Rect(0, 0, int(self.width), int(self.height))
        self.rect.center = (int(self.x), int(self.y))

        from combat.hitbox import Hitbox
        from combat.hurtbox import Hurtbox
        self.hitbox = Hitbox(self.width, self.height)
        self.hurtbox = Hurtbox(self.width, self.height)
        self.hurtbox.default_iframes = 0.05

        self.attack_box = AttackBox(
            self.width, self.height,
            damage=20, knockback=10.0
        )
        self.attack_box.active = True
        
        # Timers for attack patterns
        self.attack_cooldown = 0.0
        self.state_timer = 0.0
        self.rage_mode = False
        
        self._load_boss_animations()

    def _load_enemy_animations(self) -> None:
        # Override to prevent loading standard enemy animations
        pass
        
    def _load_boss_animations(self) -> None:
        import os
        from rendering.animation_player import Animation, Frame
        
        # Clear any existing animations (just in case)
        if hasattr(self, 'animation_player') and self.animation_player:
            self.animation_player.animations.clear()
            
        base_dir = os.path.join("assets", "images", "bosses", self.boss_type)
        if not os.path.isdir(base_dir):
            return
            
        # Standard fallback frame
        fallback_frame = None
            
        for action in os.listdir(base_dir):
            action_dir = os.path.join(base_dir, action)
            if not os.path.isdir(action_dir):
                continue
                
            files = [
                f for f in os.listdir(action_dir)
                if os.path.isfile(os.path.join(action_dir, f))
                and f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
            ]
            files = self._sort_files_numeric(files)
            frames = []
            
            for f in files:
                abs_path = os.path.abspath(os.path.join(action_dir, f))
                cache_key = f"boss_{self.boss_type}_{action}_{f}"
                surf = self.sprite_renderer.load_sprite(cache_key, abs_path)
                if surf:
                    frames.append(Frame(surf, 1.0 / 12.0))
                    if fallback_frame is None:
                        fallback_frame = surf
                
            if frames:
                loop = action not in ("death", "hurt")
                self.animation_player.add_animation(Animation(action, frames, loop=loop))
                
        if fallback_frame:
            self.sprite_renderer.sprite_cache["boss"] = fallback_frame

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float, player=None, projectile_pool=None) -> None:
        super().update(dt)

        # Phase 2 transition at 50% HP
        if self.health < self.max_health * 0.5 and self.phase == 1:
            self.phase = 2
            self._base_color = (255, 50, 200)
            self.color = self._base_color
            self.speed = 140.0
            self.attack_box.damage = 30

    def _update_animations(self, dt: float) -> None:
        if not hasattr(self, 'animation_player') or not self.animation_player:
            return
            
        speed = (self.velocity_x * self.velocity_x + self.velocity_y * self.velocity_y) ** 0.5
        anim_state = self.state.lower()
        
        if self.is_dead and "death" in self.animation_player.animations:
            anim_state = "death"
        elif self._hurt_anim_timer > 0 and "hurt" in self.animation_player.animations:
            anim_state = "hurt"
        elif anim_state not in self.animation_player.animations:
            # Fallbacks if specific state animation missing
            if speed > 0.1 and "move" in self.animation_player.animations:
                anim_state = "move"
            elif "idle" in self.animation_player.animations:
                anim_state = "idle"
                
        if anim_state in self.animation_player.animations:
            self.animation_player.play(anim_state)
            
        self.animation_player.update(dt)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(self, surface: pygame.Surface,
               offset_x: int = 0, offset_y: int = 0) -> None:
        if self.hurtbox and self.hurtbox.should_blink():
            return

        flip_x = self.velocity_x < 0
        tint = (255, 150, 150) if self._flash_timer > 0 else None
        
        sprite = "boss"
        if hasattr(self, 'animation_player') and self.animation_player and self.animation_player.get_current_sprite():
            sprite = self.animation_player.get_current_sprite()

        self.sprite_renderer.render_sprite_to_size(
            surface, sprite, self.x, self.y,
            self.width, self.height,
            offset_x, offset_y, flip_x=flip_x, tint=tint
        )

        # Name tag
        render_rect = self.rect.move(-offset_x, -offset_y)
        font = pygame.font.SysFont(None, 24)
        name_surf = font.render(self.name, True, (255, 255, 255))
        name_rect = name_surf.get_rect(midbottom=(render_rect.centerx, render_rect.top - 10))
        surface.blit(name_surf, name_rect)

    def render_ui(self, surface: pygame.Surface, camera) -> None:
        """Full-width boss health bar at top of screen."""
        bar_width = WINDOW_WIDTH - 200
        bar_x = 100
        bar_y = 50

        pygame.draw.rect(surface, (30, 30, 30),   (bar_x - 2, bar_y - 2, bar_width + 4, 24))
        pygame.draw.rect(surface, (60, 10, 60),   (bar_x, bar_y, bar_width, 20))
        ratio = max(0.0, self.health / self.max_health)
        phase_color = (150, 50, 200) if self.phase == 1 else (255, 50, 200)
        pygame.draw.rect(surface, phase_color, (bar_x, bar_y, int(bar_width * ratio), 20))

        font = pygame.font.SysFont(None, 22)
        label = font.render(f"{self.name}  [{int(self.health)}/{int(self.max_health)}]",
                            True, (255, 255, 255))
        surface.blit(label, (bar_x + 4, bar_y + 2))
