import pygame
from settings import *
from combat.hitbox import Hitbox, AttackBox
from combat.hurtbox import Hurtbox


class Entity:
    """
    Base class for all game entities (player, enemy, NPC, boss).
    Owns: position, velocity, hitbox, hurtbox, health, knockback.
    Does NOT own rendering details — subclasses handle that.
    """

    def __init__(self, x: float, y: float,
                 width: float, height: float, color: tuple):
        self.x = float(x)
        self.y = float(y)
        self.width = float(width)
        self.height = float(height)
        self.color = color

        self.visible: bool = True
        self.in_view: bool = True

        self.velocity_x: float = 0.0
        self.velocity_y: float = 0.0
        self.speed: float = 200.0

        # Pygame rect kept in sync for rendering and quick broadphase checks
        self.rect = pygame.Rect(0, 0, int(self.width), int(self.height))
        self.rect.center = (int(self.x), int(self.y))

        # Combat components
        self.hitbox:    Hitbox     = Hitbox(self.width, self.height)
        self.hurtbox:   Hurtbox    = Hurtbox(self.width, self.height)
        self.attack_box: AttackBox | None = None

        # Health
        self.max_health: float = 100.0
        self.health:     float = 100.0
        self.is_dead:    bool  = False

        # Knockback (world-space impulse, decays each frame)
        self.knockback_x: float = 0.0
        self.knockback_y: float = 0.0
        self._knockback_friction: float = 0.85   # per-frame multiplier

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def handle_movement(self, dt: float) -> None:
        """Apply velocity and knockback, then sync components."""
        # Decay knockback
        self.knockback_x *= self._knockback_friction
        self.knockback_y *= self._knockback_friction

        # Snap small knockback to zero to avoid endless micro-drift
        if abs(self.knockback_x) < 0.5:
            self.knockback_x = 0.0
        if abs(self.knockback_y) < 0.5:
            self.knockback_y = 0.0

        # Move
        self.x += (self.velocity_x + self.knockback_x) * dt
        self.y += (self.velocity_y + self.knockback_y) * dt

        # Sync rects
        self.rect.center = (int(self.x), int(self.y))
        self.hitbox.update(self.x, self.y)
        self.hurtbox.update(self.x, self.y, dt)
        if self.attack_box:
            self.attack_box.update(self.x, self.y)

    def update(self, dt: float) -> None:
        self.handle_movement(dt)
        if self.health <= 0:
            self.health = 0
            self.is_dead = True

    # ------------------------------------------------------------------
    # Combat
    # ------------------------------------------------------------------

    def take_damage(self, amount: float, source) -> None:
        """
        Apply damage from source.
        source can be any entity or projectile with .x / .y attributes.
        """
        if self.hurtbox and self.hurtbox.is_invincible():
            return

        self.health -= amount

        # Grant i-frames
        if self.hurtbox:
            self.hurtbox.grant_invincibility(self.hurtbox.default_iframes)

        if self.health <= 0:
            self.health = 0
            self.is_dead = True

        # Apply knockback away from source
        src_x = getattr(source, 'x', None)
        src_y = getattr(source, 'y', None)
        if src_x is not None and src_y is not None:
            dx = self.x - src_x
            dy = self.y - src_y
            dist = (dx * dx + dy * dy) ** 0.5
            if dist > 0:
                # Pull knockback force from attacker's attack_box if available
                atk = getattr(source, 'attack_box', None)
                force = (atk.knockback if atk else 4.0) * 120.0
                self.knockback_x = (dx / dist) * force
                self.knockback_y = (dy / dist) * force

    def heal(self, amount: float) -> None:
        self.health = min(self.health + amount, self.max_health)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(self, surface: pygame.Surface,
               offset_x: int = 0, offset_y: int = 0) -> None:
        # Blink while invincible
        if self.hurtbox and self.hurtbox.should_blink():
            return

        render_rect = self.rect.move(-offset_x, -offset_y)
        pygame.draw.rect(surface, self.color, render_rect)

    def _render_health_bar(self, surface: pygame.Surface, render_rect: pygame.Rect) -> None:
        if self.health >= self.max_health:
            return
        bar_w = int(self.width)
        bar_h = 4
        bar_x = render_rect.x
        bar_y = render_rect.y - 8
        ratio  = max(0.0, self.health / self.max_health)
        pygame.draw.rect(surface, (60, 10, 10),  (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(surface, (220, 40, 40), (bar_x, bar_y, int(bar_w * ratio), bar_h))

    def render_debug(self, surface: pygame.Surface,
                     offset_x: int = 0, offset_y: int = 0) -> None:
        """Draw hitbox (green), hurtbox (red), attack box (yellow)."""
        if self.hitbox:
            hb = self.hitbox.rect.move(-offset_x, -offset_y)
            pygame.draw.rect(surface, (0, 255, 0), hb, 1)

        if self.hurtbox:
            hurt = self.hurtbox.rect.move(-offset_x, -offset_y)
            pygame.draw.rect(surface, (255, 0, 0), hurt, 1)

        if self.attack_box and self.attack_box.active:
            atk = self.attack_box.rect.move(-offset_x, -offset_y)
            pygame.draw.rect(surface, (255, 255, 0), atk, 1)
