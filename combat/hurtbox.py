import pygame
from combat.hitbox import BoxComponent


class Hurtbox(BoxComponent):
    """
    Damage-receiving box — attached to every damageable entity.
    Tracks invulnerability frames so the entity can't be hit every single frame.
    """

    def __init__(self, width: float, height: float,
                 offset_x: float = 0.0, offset_y: float = 0.0):
        super().__init__(width, height, offset_x, offset_y)
        self.invincibility_timer: float = 0.0
        self.default_iframes: float = 0.25   # seconds — override per entity type

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, center_x: float, center_y: float, dt: float = 0.0) -> None:
        """Call every frame. Ticks down invulnerability timer."""
        super().update(center_x, center_y)
        if self.invincibility_timer > 0.0:
            self.invincibility_timer = max(0.0, self.invincibility_timer - dt)

    # ------------------------------------------------------------------
    # Invulnerability API
    # ------------------------------------------------------------------

    def is_invincible(self) -> bool:
        return self.invincibility_timer > 0.0

    def grant_invincibility(self, duration: float) -> None:
        """Set invincibility for at least `duration` seconds."""
        self.invincibility_timer = max(self.invincibility_timer, duration)

    # ------------------------------------------------------------------
    # Blink helper for rendering
    # ------------------------------------------------------------------

    def should_blink(self, blink_hz: float = 10.0) -> bool:
        """
        Returns True on 'off' blink frames while invincible.
        blink_hz controls blinks per second (default 10 = 100ms per blink phase).
        """
        if not self.is_invincible():
            return False
        return int(self.invincibility_timer * blink_hz * 2) % 2 == 0
