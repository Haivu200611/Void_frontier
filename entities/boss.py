import pygame
from entities.enemy import DummyEnemy
from combat.hitbox import AttackBox
from settings import *


class Boss(DummyEnemy):
    """
    Boss entity — larger, tougher, multi-phase.
    Inherits from DummyEnemy; driven by EnemyAI with an aggro_radius override.
    """

    def __init__(self, x: float, y: float, name: str = "MECHA BEAST"):
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

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(self, surface: pygame.Surface,
               offset_x: int = 0, offset_y: int = 0) -> None:
        if self.hurtbox and self.hurtbox.should_blink():
            return

        render_rect = self.rect.move(-offset_x, -offset_y)
        pygame.draw.rect(surface, self.color, render_rect)

        # Decorative inner outline
        inner = render_rect.inflate(-12, -12)
        pygame.draw.rect(surface, (255, 255, 255), inner, 2)

        # Name tag
        font = pygame.font.SysFont(None, 20)
        name_surf = font.render(self.name, True, (255, 255, 255))
        name_rect = name_surf.get_rect(midbottom=(render_rect.centerx, render_rect.top - 4))
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
