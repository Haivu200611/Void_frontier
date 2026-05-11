import pygame


class BoxComponent:
    """Base axis-aligned bounding box component used by hitbox / hurtbox / attackbox."""

    def __init__(self, width: float, height: float,
                 offset_x: float = 0.0, offset_y: float = 0.0):
        self.rect = pygame.Rect(0, 0, int(width), int(height))
        self.offset_x = float(offset_x)
        self.offset_y = float(offset_y)

    def update(self, center_x: float, center_y: float) -> None:
        self.rect.centerx = int(center_x + self.offset_x)
        self.rect.centery = int(center_y + self.offset_y)


class Hitbox(BoxComponent):
    """
    Physical collision box — used for wall/obstacle and entity-entity collision.
    Should match (or be slightly smaller than) the entity's visual body.
    """
    pass


class AttackBox(BoxComponent):
    """
    Melee or ranged damage box.
    Only deals damage while `active` is True.
    Combat manager checks attacker.attack_box vs defender.hurtbox.
    """

    def __init__(self, width: float, height: float,
                 offset_x: float = 0.0, offset_y: float = 0.0,
                 damage: float = 10.0, knockback: float = 5.0):
        super().__init__(width, height, offset_x, offset_y)
        self.damage: float = damage
        self.knockback: float = knockback
        self.active: bool = False

        # Set of entity IDs already hit this swing — prevents multi-hit per attack
        self.hit_set: set = set()

    def activate(self) -> None:
        self.active = True
        self.hit_set.clear()

    def deactivate(self) -> None:
        self.active = False
        self.hit_set.clear()

    def already_hit(self, entity) -> bool:
        return id(entity) in self.hit_set

    def mark_hit(self, entity) -> None:
        self.hit_set.add(id(entity))
