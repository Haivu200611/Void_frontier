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

        from systems.items import ItemDatabase
        from rendering.sprite_renderer import get_sprite_renderer
        
        renderer = get_sprite_renderer()
        sprite_key = None
        display_width = self.width * 2
        display_height = self.height * 2
        
        if self.item_id:
            item_data = ItemDatabase.get_item(self.item_id)
            if item_data:
                # Use item's display_size if available
                if hasattr(item_data, 'display_size') and item_data.display_size:
                    display_width, display_height = item_data.display_size
                
                if item_data.icon_path:
                    sprite_key = self.item_id
                    renderer.load_sprite(sprite_key, item_data.icon_path)
                
        if not sprite_key and self.item_id and "ore" in self.item_id:
            sprite_key = "generic_ore"
            renderer.load_sprite(sprite_key, "items/resources/resources.png")
            
        if sprite_key and renderer.sprite_cache.get(sprite_key):
            renderer.render_sprite_to_size(
                surface, sprite_key, self.x, self.y,
                display_width, display_height,
                offset_x, offset_y, tint=self.color if sprite_key == "generic_ore" else None
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
        super().__init__(x, y, 16, 16, color=(255, 50, 50), item_id="medkit_small")
        self.heal_amount = 20

    def apply(self, player) -> None:
        player.health = min(player.health + self.heal_amount, player.max_health)
        self.active = False


class OxygenDrop(ItemDrop):
    def __init__(self, x: float, y: float):
        super().__init__(x, y, 16, 16, color=(0, 200, 255), item_id="oxygen_pack")
        self.oxygen_amount = 25

    def apply(self, player) -> None:
        player.oxygen = min(player.oxygen + self.oxygen_amount, player.max_oxygen)
        self.active = False


class FoodDrop(ItemDrop):
    def __init__(self, x: float, y: float):
        super().__init__(x, y, 16, 16, color=(255, 180, 50), item_id="food_pack")
        self.food_amount = 20

    def apply(self, player) -> None:
        player.hunger = min(player.hunger + self.food_amount, player.max_hunger)
        self.active = False


class ResourceDrop(ItemDrop):
    def __init__(self, x: float, y: float, item_id: str, amount: int = 1):
        super().__init__(x, y, 14, 14, color=(190, 190, 190), item_id=item_id, amount=amount)
