from __future__ import annotations

from settings import TILE_SIZE
from world.chunk import Chunk
from world.procedural_gen import MapGenerator
from world.biome_manager import BiomeManager

CHUNK_SIZE = 32


class WorldManager:
    def __init__(self, seed: str = "VOID_FRONTIER_1", world_id: str = "toxic_plains"):
        self.base_seed = seed
        self.current_world_id = world_id
        self.seed = f"{seed}:{world_id}"

        self.chunks: dict[tuple[int, int], Chunk] = {}
        self.biome_manager = BiomeManager(seed=self.seed)

    def transition_world(self, world_id: str) -> None:
        if world_id == self.current_world_id:
            return
        self.current_world_id = world_id
        self.seed = f"{self.base_seed}:{world_id}"
        self.chunks.clear()
        self.biome_manager = BiomeManager(seed=self.seed)

    def load_chunk(self, chunk_x: int, chunk_y: int) -> None:
        if (chunk_x, chunk_y) in self.chunks:
            return

        chunk_seed = f"{self.seed}_{chunk_x}_{chunk_y}"
        generator = MapGenerator(CHUNK_SIZE, CHUNK_SIZE, seed=chunk_seed)
        
        # Use flat map for Chapter 1 (toxic_plains) and Chapter 4 (void_ruins)
        if self.current_world_id in ["toxic_plains", "void_ruins"]:
            grid_data = generator.generate_flat()
        else:
            grid_data = generator.generate_caves()

        biome = self.biome_manager.get_biome_for_chunk(chunk_x, chunk_y)
        chunk = Chunk(
            chunk_x,
            chunk_y,
            grid_data,
            biome_id=biome.biome_id,
            terrain_color=biome.terrain_color,
        )
        
        # Chapter 1 (toxic_plains) has no obstacles
        if self.current_world_id == "toxic_plains":
            chunk.obstacles = []
            
        self.chunks[(chunk_x, chunk_y)] = chunk

    def get_chunk_coords(self, world_x: float, world_y: float) -> tuple[int, int]:
        return (
            int(world_x // (CHUNK_SIZE * TILE_SIZE)),
            int(world_y // (CHUNK_SIZE * TILE_SIZE)),
        )

    def get_loaded_chunk_keys_near(self, world_x: float, world_y: float, radius: int = 2) -> list[tuple[int, int]]:
        chunk_x, chunk_y = self.get_chunk_coords(world_x, world_y)
        keys: list[tuple[int, int]] = []
        for cy in range(chunk_y - radius, chunk_y + radius + 1):
            for cx in range(chunk_x - radius, chunk_x + radius + 1):
                if (cx, cy) not in self.chunks:
                    self.load_chunk(cx, cy)
                keys.append((cx, cy))
        return keys

    def get_obstacles_near(self, world_x: float, world_y: float) -> list:
        keys = self.get_loaded_chunk_keys_near(world_x, world_y, radius=2)
        obstacles = []
        for key in keys:
            obstacles.extend(self.chunks[key].obstacles)
        return obstacles

    def render(self, surface, offset_x: int, offset_y: int, world_x: float, world_y: float, debug_mode: bool = False) -> list[tuple[int, int]]:
        keys = self.get_loaded_chunk_keys_near(world_x, world_y, radius=2)
        for key in keys:
            self.chunks[key].render(surface, offset_x, offset_y)

            if debug_mode:
                chunk = self.chunks[key]
                px = key[0] * CHUNK_SIZE * TILE_SIZE - offset_x
                py = key[1] * CHUNK_SIZE * TILE_SIZE - offset_y
                import pygame

                rect = pygame.Rect(px, py, CHUNK_SIZE * TILE_SIZE, CHUNK_SIZE * TILE_SIZE)
                pygame.draw.rect(surface, (80, 80, 110), rect, 1)

        return keys
