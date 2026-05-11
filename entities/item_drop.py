from __future__ import annotations

import pygame

from combat.hitbox import BoxComponent


class ItemDrop:
    def __init__(
        self,
        x: float,
        y: float,
        width: int = 16,
        height: int = 16,
        color: tuple[int, int, int] = (0, 255, 0),
        item_id: str | None = None,
        amount: int = 1,
    ):
        self.x = float(x)
        self.y = float(y)
        self.width = width
        self.height = height
        self.color = color
        self.item_id = item_id
        self.amount = amount

        self.hitbox = BoxComponent(width, height)
        self.hitbox.update(x, y)
        self.active = True

    def update(self, dt: float) -> None:
        self.hitbox.update(self.x, self.y)

    def apply(self, player) -> None:
        if self.item_id and hasattr(player, "inventory"):
            leftover = player.inventory.add_item(self.item_id, self.amount)
            if leftover <= 0:
                self.active = False
                return
            self.amount = leftover
            return
        self.active = False

    def render(self, surface: pygame.Surface, offset_x: int = 0, offset_y: int = 0) -> None:
        if not self.active:
            return

        if not hasattr(self, 'sprite_renderer'):
            from rendering.sprite_renderer import SpriteRenderer
            self.sprite_renderer = SpriteRenderer()
            # If it's a resource, use the rock sprite
            if self.item_id and "ore" in self.item_id:
                self.sprite_renderer.load_sprite("item", "items/resources/resources.png")
            else:
                # Fallback to a generic box for now or a generic item sprite if we had one
                pass

        if hasattr(self, 'sprite_renderer') and self.sprite_renderer.sprite_cache.get("item"):
            self.sprite_renderer.render_sprite(
                surface, "item", self.x, self.y,
                offset_x, offset_y, scale=0.4, tint=self.color
            )
        else:
            # Fallback to rect
            rect = self.hitbox.rect.copy()
            rect.x -= offset_x
            rect.y -= offset_y
            pygame.draw.rect(surface, self.color, rect)
            pygame.draw.rect(surface, (255, 255, 255), rect, 1)


class HealthDrop(ItemDrop):
    def __init__(self, x: float, y: float):
        super().__init__(x, y, 16, 16, color=(255, 50, 50))
        self.heal_amount = 20

    def apply(self, player) -> None:
        player.health = min(player.health + self.heal_amount, player.max_health)
        self.active = False


class OxygenDrop(ItemDrop):
    def __init__(self, x: float, y: float):
        super().__init__(x, y, 16, 16, color=(0, 200, 255))
        self.oxygen_amount = 25

    def apply(self, player) -> None:
        player.oxygen = min(player.oxygen + self.oxygen_amount, player.max_oxygen)
        self.active = False


class FoodDrop(ItemDrop):
    def __init__(self, x: float, y: float):
        super().__init__(x, y, 16, 16, color=(255, 180, 50))
        self.food_amount = 20

    def apply(self, player) -> None:
        player.hunger = min(player.hunger + self.food_amount, player.max_hunger)
        self.active = False


class ResourceDrop(ItemDrop):
    def __init__(self, x: float, y: float, item_id: str, amount: int = 1):
        super().__init__(x, y, 14, 14, color=(190, 190, 190), item_id=item_id, amount=amount)
