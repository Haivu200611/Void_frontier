from __future__ import annotations

import math
import random
from typing import Iterable

from settings import WINDOW_WIDTH, WINDOW_HEIGHT, TILE_SIZE
from entities.enemy import DummyEnemy
from entities.ore import Ore, ORE_PROFILES
from ai.enemy_ai import EnemyAI


class SpawnZone:
    """Defines a circular region where enemies can spawn."""

    def __init__(self, cx: float, cy: float, radius: float, weight: float = 1.0, max_enemies: int = 5):
        self.cx = cx
        self.cy = cy
        self.radius = radius
        self.weight = weight
        self.max_enemies = max_enemies


class SpawnManager:
    """
    Handles enemy spawning and biome-aware resource (ore) spawning.
    """

    def __init__(self):
        # Enemy spawning
        self.min_spawn_dist: float = max(WINDOW_WIDTH, WINDOW_HEIGHT) * 0.55
        self.max_spawn_dist: float = max(WINDOW_WIDTH, WINDOW_HEIGHT) * 1.4
        self.despawn_dist: float = self.max_spawn_dist * 1.6

        self.spawn_cooldown: float = 3.5
        self.spawn_timer: float = 1.0
        
        self.max_enemies: int = 15
        self.zones: list[SpawnZone] = []

        # Resource spawning
        self.ores_by_chunk: dict[tuple[int, int], list[Ore]] = {}

    def configure_for_world(self, world_id: str) -> None:
        if world_id == "toxic_plains":
            self.max_enemies = 30
            self.spawn_cooldown = 1.2
        elif world_id == "void_ruins":
            self.max_enemies = 25
            self.spawn_cooldown = 2.0
        else:
            self.max_enemies = 15
            self.spawn_cooldown = 3.5

    # ------------------------------------------------------------------
    # Enemy update
    # ------------------------------------------------------------------

    def update(self, dt: float, player, enemies: list, enemy_ais: list) -> None:
        self._handle_despawn(player, enemies)

        if len(enemies) >= self.max_enemies:
            return

        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_timer = self.spawn_cooldown
            self._spawn_enemy(player, enemies, enemy_ais)

    # ------------------------------------------------------------------
    # Resource spawning
    # ------------------------------------------------------------------

    def sync_ore_spawns(self, world_manager, biome_manager, loaded_chunk_keys: Iterable[tuple[int, int]]) -> None:
        for key in loaded_chunk_keys:
            if key in self.ores_by_chunk:
                continue
            chunk = world_manager.chunks.get(key)
            if chunk is None:
                continue
            biome = biome_manager.get_biome_for_chunk(key[0], key[1])
            self.ores_by_chunk[key] = self._generate_ores_for_chunk(
                world_manager.seed,
                key[0],
                key[1],
                chunk.grid_data,
                biome.ore_types,
                biome.resource_spawn_modifier,
            )

    def get_ores_near(self, loaded_chunk_keys: Iterable[tuple[int, int]]) -> list[Ore]:
        ores: list[Ore] = []
        for key in loaded_chunk_keys:
            ores.extend(self.ores_by_chunk.get(key, []))
        return ores

    def update_ores(self, dt: float, loaded_chunk_keys: Iterable[tuple[int, int]]) -> None:
        for ore in self.get_ores_near(loaded_chunk_keys):
            ore.update(dt)

    def _generate_ores_for_chunk(
        self,
        world_seed: str,
        chunk_x: int,
        chunk_y: int,
        grid_data: list[list[int]],
        biome_ore_types: tuple[str, ...],
        spawn_modifier: float,
    ) -> list[Ore]:
        rng = random.Random(f"ore:{world_seed}:{chunk_x}:{chunk_y}")

        floor_tiles: list[tuple[int, int]] = []
        for y, row in enumerate(grid_data):
            for x, tile in enumerate(row):
                if tile == 0:
                    floor_tiles.append((x, y))

        if not floor_tiles:
            return []

        spawn_count = max(1, int(rng.randint(3, 7) * spawn_modifier))
        ores: list[Ore] = []
        for idx in range(spawn_count):
            tx, ty = floor_tiles[rng.randrange(0, len(floor_tiles))]
            wx = chunk_x * 32 * TILE_SIZE + tx * TILE_SIZE + TILE_SIZE * 0.5
            wy = chunk_y * 32 * TILE_SIZE + ty * TILE_SIZE + TILE_SIZE * 0.5

            ore_type = self._pick_ore_type(rng, biome_ore_types)
            node_id = f"ore:{chunk_x}:{chunk_y}:{tx}:{ty}:{idx}"
            ores.append(Ore(wx, wy, ore_type=ore_type, node_id=node_id))

        return ores

    def _pick_ore_type(self, rng: random.Random, biome_ore_types: tuple[str, ...]) -> str:
        candidates = []
        for ore_type, profile in ORE_PROFILES.items():
            if biome_ore_types and ore_type not in biome_ore_types:
                continue
            candidates.append((ore_type, profile.rarity))

        if not candidates:
            return "Iron Ore"

        total = sum(weight for _, weight in candidates)
        roll = rng.uniform(0, total)
        acc = 0.0
        for ore_type, weight in candidates:
            acc += weight
            if roll <= acc:
                return ore_type
        return candidates[-1][0]

    # ------------------------------------------------------------------
    # Enemy helpers
    # ------------------------------------------------------------------

    def _spawn_enemy(self, player, enemies: list, enemy_ais: list) -> None:
        spawn_x, spawn_y = self._pick_spawn_point(player)

        enemy = DummyEnemy(spawn_x, spawn_y)
        ai = EnemyAI(enemy)

        enemies.append(enemy)
        enemy_ais.append(ai)

    def _pick_spawn_point(self, player) -> tuple[float, float]:
        if self.zones:
            zone = self._pick_zone()
            angle = random.uniform(0, math.tau)
            radius = random.uniform(0, zone.radius)
            return (zone.cx + math.cos(angle) * radius, zone.cy + math.sin(angle) * radius)

        angle = random.uniform(0, math.tau)
        dist = random.uniform(self.min_spawn_dist, self.max_spawn_dist)
        return (player.x + math.cos(angle) * dist, player.y + math.sin(angle) * dist)

    def _pick_zone(self) -> SpawnZone:
        total = sum(z.weight for z in self.zones)
        r = random.uniform(0, total)
        acc = 0.0
        for z in self.zones:
            acc += z.weight
            if r <= acc:
                return z
        return self.zones[-1]

    def _handle_despawn(self, player, enemies: list) -> None:
        for enemy in enemies:
            dist = math.hypot(enemy.x - player.x, enemy.y - player.y)
            if dist > self.despawn_dist:
                enemy.is_dead = True

    # ------------------------------------------------------------------
    # Zone API
    # ------------------------------------------------------------------

    def add_zone(self, cx: float, cy: float, radius: float, weight: float = 1.0, max_enemies: int = 5) -> None:
        self.zones.append(SpawnZone(cx, cy, radius, weight, max_enemies))

    def clear_zones(self) -> None:
        self.zones.clear()
