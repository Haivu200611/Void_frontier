import pygame
from combat.hitbox import AttackBox


class Projectile:
    """
    Single projectile instance managed by ProjectilePool.
    Moves in a straight line; deactivates on lifetime expiry or wall hit.
    """

    def __init__(self, x: float, y: float,
                 dir_x: float, dir_y: float,
                 speed: float, lifetime: float,
                 damage: float,
                 color: tuple = (255, 220, 0),
                 radius: int = 5,
                 owner_layer: str = "player"):

        self.x = float(x)
        self.y = float(y)
        self.dir_x = float(dir_x)
        self.dir_y = float(dir_y)
        self.speed = float(speed)
        self.lifetime = float(lifetime)
        self.max_lifetime = float(lifetime)
        self.color = color
        self.radius = radius
        self.owner_layer = owner_layer   # "player" or "enemy" — for filtering
        self.active = True
        self.should_create_particles = True
        self.hit_something = False

        # Attack box used by CombatManager
        self.attack_box = AttackBox(radius * 2, radius * 2, damage=damage, knockback=2.0)
        self.attack_box.active = True
        self.attack_box.update(self.x, self.y)

        # Needed so Entity.take_damage can read source position
        # (projectiles are not Entities but share the x/y interface)

    # ------------------------------------------------------------------
    # Update / deactivate
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        if not self.active:
            return

        self.x += self.dir_x * self.speed * dt
        self.y += self.dir_y * self.speed * dt

        self.lifetime -= dt
        if self.lifetime <= 0:
            self.deactivate()
            return

        self.attack_box.update(self.x, self.y)

    def deactivate(self) -> None:
        self.active = False
        self.attack_box.active = False

    def reset(self, x: float, y: float,
              dir_x: float, dir_y: float,
              speed: float, lifetime: float,
              damage: float,
              color: tuple, radius: int,
              owner_layer: str) -> None:
        """Reinitialise a pooled projectile without allocation."""
        self.x = float(x)
        self.y = float(y)
        self.dir_x = dir_x
        self.dir_y = dir_y
        self.speed = speed
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.color = color
        self.radius = radius
        self.owner_layer = owner_layer
        self.active = True
        self.hit_something = False

        self.attack_box.rect.width  = radius * 2
        self.attack_box.rect.height = radius * 2
        self.attack_box.damage = damage
        self.attack_box.active = True
        self.attack_box.hit_set.clear()
        self.attack_box.update(x, y)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(self, surface: pygame.Surface,
               offset_x: int = 0, offset_y: int = 0) -> None:
        if not self.active:
            return

        sx = int(self.x - offset_x)
        sy = int(self.y - offset_y)

        # Glow effect (outer dim circle + bright core)
        glow_r = self.radius + 3
        glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        glow_color = (*self.color, 60)
        pygame.draw.circle(glow_surf, glow_color, (glow_r, glow_r), glow_r)
        surface.blit(glow_surf, (sx - glow_r, sy - glow_r))

        pygame.draw.circle(surface, self.color, (sx, sy), self.radius)
        pygame.draw.circle(surface, (255, 255, 255), (sx, sy), max(1, self.radius - 2))

    def render_debug(self, surface: pygame.Surface,
                     offset_x: int = 0, offset_y: int = 0) -> None:
        if not self.active:
            return
        atk = self.attack_box.rect.move(-offset_x, -offset_y)
        pygame.draw.rect(surface, (255, 100, 0), atk, 1)
        # Draw trajectory line
        end_x = int(self.x + self.dir_x * 60 - offset_x)
        end_y = int(self.y + self.dir_y * 60 - offset_y)
        pygame.draw.line(surface, (255, 255, 0),
                         (int(self.x - offset_x), int(self.y - offset_y)),
                         (end_x, end_y), 1)


class ProjectilePool:
    """
    Object pool for projectiles — avoids per-frame allocation.
    Inactive projectiles are reused via reset().
    """

    def __init__(self, max_projectiles: int = 200):
        self.pool: list[Projectile] = []
        self.max_projectiles = max_projectiles

    def spawn(self, x: float, y: float,
              dir_x: float, dir_y: float,
              speed: float, lifetime: float,
              damage: float,
              color: tuple = (255, 220, 0),
              radius: int = 5,
              owner_layer: str = "player") -> Projectile | None:

        # Normalise direction
        length = (dir_x * dir_x + dir_y * dir_y) ** 0.5
        if length == 0:
            return None
        dir_x /= length
        dir_y /= length

        # Reuse inactive slot
        for p in self.pool:
            if not p.active:
                p.reset(x, y, dir_x, dir_y, speed, lifetime,
                        damage, color, radius, owner_layer)
                return p

        # Allocate new if under cap
        if len(self.pool) < self.max_projectiles:
            p = Projectile(x, y, dir_x, dir_y, speed, lifetime,
                           damage, color, radius, owner_layer)
            self.pool.append(p)
            return p

        return None  # Pool full

    def update(self, dt: float) -> None:
        for p in self.pool:
            if p.active:
                p.update(dt)

    def check_wall_collisions(self, obstacles: list) -> None:
        """Deactivate projectiles that hit solid obstacles."""
        for p in self.pool:
            if not p.active:
                continue
            for obs in obstacles:
                if hasattr(obs, 'rect') and p.attack_box.rect.colliderect(obs.rect):
                    p.hit_something = True
                    p.deactivate()
                    break

    def get_active_projectiles(self) -> list:
        return [p for p in self.pool if p.active]

    def get_active_count(self) -> int:
        return sum(1 for p in self.pool if p.active)

    def render(self, surface: pygame.Surface,
               offset_x: int = 0, offset_y: int = 0) -> None:
        for p in self.pool:
            if p.active:
                p.render(surface, offset_x, offset_y)

    def render_debug(self, surface: pygame.Surface,
                     offset_x: int = 0, offset_y: int = 0) -> None:
        for p in self.pool:
            if p.active:
                p.render_debug(surface, offset_x, offset_y)
