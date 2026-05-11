import pygame
import math
import random
from settings import WINDOW_WIDTH, WINDOW_HEIGHT


class Camera:
    """
    Smooth follow camera with lerp movement, clamping, and screen shake.
    Supports large worlds by treating all entities in world-space coordinates.
    """

    def __init__(self, screen_width: int = WINDOW_WIDTH, screen_height: int = WINDOW_HEIGHT):
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Current camera world position (top-left corner of the view)
        self.offset = pygame.math.Vector2(0.0, 0.0)

        # Desired camera position (before lerp)
        self.target_offset = pygame.math.Vector2(0.0, 0.0)

        # Lerp speed (higher = snappier follow, 8-12 feels smooth for most games)
        self.lerp_speed: float = 8.0

        # World bounds — set via set_bounds() to clamp camera inside world
        self.bounds: pygame.Rect | None = None

        # Screen shake
        self.shake_duration: float = 0.0
        self.shake_intensity: float = 0.0
        self.shake_offset: pygame.math.Vector2 = pygame.math.Vector2(0.0, 0.0)

        # Internal rect for compatibility
        self.camera_rect = pygame.Rect(0, 0, screen_width, screen_height)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_bounds(self, world_width: int, world_height: int) -> None:
        """Constrain camera within a world of given pixel dimensions."""
        self.bounds = pygame.Rect(0, 0, world_width, world_height)

    def add_shake(self, intensity: float, duration: float) -> None:
        """
        Trigger screen shake.
        :param intensity: Max pixel offset per frame.
        :param duration:  Duration in seconds.
        """
        self.shake_intensity = max(self.shake_intensity, intensity)
        self.shake_duration = max(self.shake_duration, duration)

    def update(self, target, dt: float) -> None:
        """
        Update camera each frame. Smoothly follows target using dt-based lerp.
        :param target: Any object with .rect or .x/.y attributes (world-space).
        :param dt:     Delta time in seconds.
        """
        # Resolve target world position
        if hasattr(target, 'rect'):
            tx = float(target.rect.centerx)
            ty = float(target.rect.centery)
        elif hasattr(target, 'pos'):
            tx = float(target.pos.x)
            ty = float(target.pos.y)
        else:
            tx = float(getattr(target, 'x', 0))
            ty = float(getattr(target, 'y', 0))

        # Compute desired offset so target is centered on screen
        self.target_offset.x = tx - self.screen_width * 0.5
        self.target_offset.y = ty - self.screen_height * 0.5

        # Frame-rate-independent exponential lerp:
        #   result = target + (current - target) * e^(-speed * dt)
        factor = 1.0 - math.exp(-self.lerp_speed * dt)
        self.offset.x += (self.target_offset.x - self.offset.x) * factor
        self.offset.y += (self.target_offset.y - self.offset.y) * factor

        # Clamp to world bounds
        if self.bounds:
            self.offset.x = max(self.bounds.left,
                                min(self.offset.x, self.bounds.right - self.screen_width))
            self.offset.y = max(self.bounds.top,
                                min(self.offset.y, self.bounds.bottom - self.screen_height))

        # Update shake
        self._update_shake(dt)

        # Sync internal rect
        self.camera_rect.topleft = (int(self.offset.x), int(self.offset.y))

    # ------------------------------------------------------------------
    # Coordinate helpers
    # ------------------------------------------------------------------

    def apply(self, entity) -> pygame.Rect:
        """Return a screen-space Rect for an entity (has .rect)."""
        total = self._total_offset()
        if hasattr(entity, 'rect'):
            return entity.rect.move(-int(total.x), -int(total.y))
        pos = getattr(entity, 'pos',
                      pygame.math.Vector2(getattr(entity, 'x', 0), getattr(entity, 'y', 0)))
        return pygame.Rect(int(pos.x - total.x), int(pos.y - total.y), 0, 0)

    def apply_rect(self, rect: pygame.Rect) -> pygame.Rect:
        """Apply camera offset to any pygame.Rect (world-space → screen-space)."""
        total = self._total_offset()
        return rect.move(-int(total.x), -int(total.y))

    def get_offset(self) -> pygame.math.Vector2:
        """
        Return total offset (camera + shake) as a Vector2.
        Use offset_x = int(cam.get_offset().x) before drawing.
        """
        return self._total_offset()

    def world_to_screen(self, wx: float, wy: float):
        """Convert world coordinates to screen coordinates."""
        total = self._total_offset()
        return (wx - total.x, wy - total.y)

    def screen_to_world(self, sx: float, sy: float):
        """Convert screen coordinates to world coordinates."""
        total = self._total_offset()
        return (sx + total.x, sy + total.y)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _total_offset(self) -> pygame.math.Vector2:
        return pygame.math.Vector2(
            self.offset.x + self.shake_offset.x,
            self.offset.y + self.shake_offset.y
        )

    def _update_shake(self, dt: float) -> None:
        if self.shake_duration > 0:
            self.shake_duration -= dt
            if self.shake_duration <= 0:
                self.shake_duration = 0.0
                self.shake_intensity = 0.0
                self.shake_offset.update(0, 0)
            else:
                # Decay intensity as shake winds down for a natural feel
                decay = self.shake_duration / max(self.shake_duration + dt, 0.001)
                intensity = self.shake_intensity * decay
                self.shake_offset.x = random.uniform(-intensity, intensity)
                self.shake_offset.y = random.uniform(-intensity, intensity)
        else:
            self.shake_offset.update(0, 0)
