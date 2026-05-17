from __future__ import annotations

from dataclasses import dataclass

import pygame

from entities.entity import Entity
from combat.hitbox import Hitbox


class OreType:
    IRON = "Iron Ore"
    CRYSTAL = "Crystal Ore"
    TOXIC = "Toxic Ore"
    VOID = "Void Fragment"
    METEOR = "Meteor Ore"


@dataclass(frozen=True)
class OreProfile:
    ore_type: str
    max_health: float
    hardness: int
    drop_id: str
    drop_amount: tuple[int, int]
    rarity: float
    spawn_biomes: tuple[str, ...]
    respawn_time: float
    color: tuple[int, int, int]


ORE_PROFILES: dict[str, OreProfile] = {
    OreType.IRON: OreProfile(
        ore_type=OreType.IRON,
        max_health=90,
        hardness=1,
        drop_id="item_iron_ore",
        drop_amount=(1, 3),
        rarity=0.65,
        spawn_biomes=("crystal_desert",),
        respawn_time=42.0,
        color=(155, 155, 160),
    ),
    OreType.CRYSTAL: OreProfile(
        ore_type=OreType.CRYSTAL,
        max_health=170,
        hardness=2,
        drop_id="item_crystal_ore",
        drop_amount=(1, 2),
        rarity=0.28,
        spawn_biomes=("crystal_desert", "fungal_cave"),
        respawn_time=64.0,
        color=(65, 200, 250),
    ),
    OreType.TOXIC: OreProfile(
        ore_type=OreType.TOXIC,
        max_health=140,
        hardness=2,
        drop_id="item_toxic_ore",
        drop_amount=(1, 2),
        rarity=0.22,
        spawn_biomes=("fungal_cave",),
        respawn_time=58.0,
        color=(80, 240, 90),
    ),
    OreType.VOID: OreProfile(
        ore_type=OreType.VOID,
        max_health=360,
        hardness=3,
        drop_id="item_void_fragment",
        drop_amount=(1, 1),
        rarity=0.08,
        spawn_biomes=(),
        respawn_time=90.0,
        color=(195, 85, 255),
    ),
    OreType.METEOR: OreProfile(
        ore_type=OreType.METEOR,
        max_health=220,
        hardness=2,
        drop_id="item_meteor_ore",
        drop_amount=(1, 2),
        rarity=0.25,
        spawn_biomes=("crystal_desert", "fungal_cave"),
        respawn_time=60.0,
        color=(255, 120, 50),
    ),
}


class Ore(Entity):
    def __init__(self, x: float, y: float, ore_type: str = OreType.IRON, node_id: str | None = None):
        super().__init__(x, y, 44, 44, (120, 120, 120))

        self.ore_type = ore_type
        self.profile = ORE_PROFILES.get(ore_type, ORE_PROFILES[OreType.IRON])
        self.node_id = node_id or f"ore:{int(x)}:{int(y)}:{ore_type}"

        self.max_health = self.profile.max_health
        self.health = self.max_health
        self.hardness = self.profile.hardness
        self.drop_id = self.profile.drop_id
        self.drop_amount = self.profile.drop_amount
        self.rarity = self.profile.rarity
        self.spawn_biomes = self.profile.spawn_biomes

        self.color = self.profile.color
        self.hitbox = Hitbox(self.width, self.height)
        self.hitbox.update(self.x, self.y)

        self.is_dead = False
        self.respawn_timer = 0.0
        self._feedback_timer = 0.0
        
        self.break_frames: list[str] = []
        from rendering.sprite_renderer import SpriteRenderer
        self.sprite_renderer = SpriteRenderer()
        self._load_break_frames()

    def _load_break_frames(self) -> None:
        import os
        import re
        
        folder_map = {
            OreType.IRON: "iron_ore",
            OreType.CRYSTAL: "crystal_ore",
            OreType.TOXIC: "toxic_ore",
            OreType.METEOR: "meteor_ore",
            OreType.VOID: "void_ore"
        }
        folder_name = folder_map.get(self.ore_type, "iron_ore")
        
        base_dir = os.path.join("assets", "images", "ore", folder_name)
        if not os.path.isdir(base_dir):
            # Fallback static sprite
            self.sprite_renderer.load_sprite("ore_static", "items/resources/resources.png")
            return
            
        files = [
            f for f in os.listdir(base_dir)
            if os.path.isfile(os.path.join(base_dir, f))
            and f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
        ]
        
        def key_fn(name: str) -> int:
            m = re.search(r"(\d+)", name)
            return int(m.group(1)) if m else 0
            
        files = sorted(files, key=key_fn)
        
        for f in files:
            abs_path = os.path.abspath(os.path.join(base_dir, f))
            cache_key = f"ore_{folder_name}_{f}"
            surf = self.sprite_renderer.load_sprite(cache_key, abs_path)
            if surf:
                self.break_frames.append(cache_key)
                
        if not self.break_frames:
            self.sprite_renderer.load_sprite("ore_static", "items/resources/resources.png")

    def take_mining_damage(self, amount: float, mining_power: int) -> bool:
        if self.is_dead:
            return False
        if mining_power < self.hardness:
            self._feedback_timer = 0.12
            return False

        self.health -= max(1.0, amount)
        self._feedback_timer = 0.18

        if self.health <= 0:
            self.health = 0.0
            self.is_dead = True
            self.respawn_timer = self.profile.respawn_time

        return True

    def update(self, dt: float) -> None:
        if self._feedback_timer > 0:
            self._feedback_timer = max(0.0, self._feedback_timer - dt)

        if self.is_dead:
            self.respawn_timer = max(0.0, self.respawn_timer - dt)
            if self.respawn_timer <= 0:
                self.is_dead = False
                self.health = self.max_health

    def render(self, surface: pygame.Surface, offset_x: int = 0, offset_y: int = 0) -> None:
        if self.is_dead:
            # Render ghost/empty node
            rect = self.rect.copy()
            rect.x -= offset_x
            rect.y -= offset_y
            pygame.draw.rect(surface, (35, 35, 40), rect, 1)
            return

        base_color = self.color
        if self._feedback_timer > 0:
            base_color = tuple(min(255, c + 80) for c in self.color)

        sprite = "ore_static"
        if self.break_frames:
            ratio = max(0.0, min(1.0, self.health / self.max_health))
            idx = int((1.0 - ratio) * len(self.break_frames))
            idx = min(idx, len(self.break_frames) - 1)
            sprite = self.break_frames[idx]

        # Draw sprite with tint
        self.sprite_renderer.render_sprite_to_size(
            surface, sprite, self.x, self.y,
            self.width, self.height,
            offset_x, offset_y, tint=base_color
        )

        if self.health < self.max_health:
            rect = self.rect.copy()
            rect.x -= offset_x
            rect.y -= offset_y
            bar_w = self.width
            ratio = max(0.0, self.health / self.max_health)
            pygame.draw.rect(surface, (60, 20, 20), (rect.x, rect.y - 8, bar_w, 4))
            pygame.draw.rect(surface, (70, 220, 90), (rect.x, rect.y - 8, int(bar_w * ratio), 4))

    def to_save_data(self) -> dict:
        return {
            "node_id": self.node_id,
            "ore_type": self.ore_type,
            "x": self.x,
            "y": self.y,
            "is_dead": self.is_dead,
            "health": self.health,
            "respawn_timer": self.respawn_timer,
        }

    def load_save_data(self, payload: dict) -> None:
        self.is_dead = bool(payload.get("is_dead", False))
        self.health = float(payload.get("health", self.max_health))
        self.respawn_timer = float(payload.get("respawn_timer", 0.0))
