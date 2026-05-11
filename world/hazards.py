from __future__ import annotations

import random
from dataclasses import dataclass

import pygame

from settings import TILE_SIZE


@dataclass
class HazardSpec:
    hazard_id: str
    color: tuple[int, int, int]
    dps: float
    status_effect: str | None
    move_slow: float = 1.0
    oxygen_drain: float = 0.0


HAZARD_SPECS: dict[str, HazardSpec] = {
    "toxic_zone": HazardSpec("toxic_zone", (70, 180, 70), dps=7.0, status_effect="poison", move_slow=0.9, oxygen_drain=4.5),
    "lava": HazardSpec("lava", (255, 115, 40), dps=18.0, status_effect="burn", move_slow=0.75),
    "acid_pool": HazardSpec("acid_pool", (115, 255, 80), dps=12.0, status_effect="toxic_damage", move_slow=0.85, oxygen_drain=3.0),
    "radiation_zone": HazardSpec("radiation_zone", (120, 255, 140), dps=9.0, status_effect="slow", move_slow=0.7),
}


class HazardZone:
    def __init__(self, zone_id: str, hazard_type: str, rect: pygame.Rect):
        self.zone_id = zone_id
        self.hazard_type = hazard_type
        self.rect = rect
        self.spec = HAZARD_SPECS.get(hazard_type, HAZARD_SPECS["toxic_zone"])

    def contains(self, x: float, y: float) -> bool:
        return self.rect.collidepoint(int(x), int(y))


class HazardManager:
    def __init__(self, seed: str):
        self.seed = seed
        self.zones_by_chunk: dict[tuple[int, int], list[HazardZone]] = {}

    def ensure_chunk_zones(self, chunk_x: int, chunk_y: int, biome_hazards: tuple[str, ...]) -> None:
        key = (chunk_x, chunk_y)
        if key in self.zones_by_chunk:
            return

        if not biome_hazards:
            self.zones_by_chunk[key] = []
            return

        rng = random.Random(f"{self.seed}:hazard:{chunk_x}:{chunk_y}")
        zone_count = rng.randint(0, 2)
        zones: list[HazardZone] = []

        chunk_px = chunk_x * TILE_SIZE * 32
        chunk_py = chunk_y * TILE_SIZE * 32

        for i in range(zone_count):
            hazard_type = biome_hazards[rng.randrange(0, len(biome_hazards))]
            size_tiles = rng.randint(2, 5)
            w = size_tiles * TILE_SIZE
            h = size_tiles * TILE_SIZE
            max_x = chunk_px + TILE_SIZE * 32 - w
            max_y = chunk_py + TILE_SIZE * 32 - h
            x = rng.randint(chunk_px, max_x)
            y = rng.randint(chunk_py, max_y)
            zone = HazardZone(
                zone_id=f"{chunk_x}:{chunk_y}:{i}",
                hazard_type=hazard_type,
                rect=pygame.Rect(x, y, w, h),
            )
            zones.append(zone)

        self.zones_by_chunk[key] = zones

    def get_zones_near(self, chunk_keys: list[tuple[int, int]]) -> list[HazardZone]:
        out: list[HazardZone] = []
        for key in chunk_keys:
            out.extend(self.zones_by_chunk.get(key, ()))
        return out

    def get_zone_at(self, x: float, y: float, chunk_keys: list[tuple[int, int]]) -> HazardZone | None:
        for zone in self.get_zones_near(chunk_keys):
            if zone.contains(x, y):
                return zone
        return None

    def apply_hazards(self, player, status_manager, dt: float, chunk_keys: list[tuple[int, int]]) -> HazardZone | None:
        zone = self.get_zone_at(player.x, player.y, chunk_keys)
        if not zone:
            return None

        player.health = max(0.0, player.health - zone.spec.dps * dt)
        if zone.spec.oxygen_drain > 0 and not getattr(player, 'disable_survival_drain', False):
            player.oxygen = max(0.0, player.oxygen - zone.spec.oxygen_drain * dt)
            
        if zone.spec.status_effect:
            status_manager.apply_effect(zone.spec.status_effect)
        if player.health <= 0:
            player.is_dead = True
        return zone

    def render(self, surface: pygame.Surface, offset_x: int, offset_y: int, zones: list[HazardZone], debug: bool) -> None:
        for zone in zones:
            rect = zone.rect.move(-offset_x, -offset_y)
            if debug:
                pygame.draw.rect(surface, zone.spec.color, rect, 2)
            else:
                overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                overlay.fill((*zone.spec.color, 55))
                surface.blit(overlay, rect.topleft)
