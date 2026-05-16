from __future__ import annotations

import pygame

from settings import TILE_SIZE
from world.obstacle import Obstacle


class Chunk:
    def __init__(self, chunk_x: int, chunk_y: int, grid_data: list[list[int]], biome_id: str, terrain_color: tuple[int, int, int]):
        self.chunk_x = chunk_x
        self.chunk_y = chunk_y
        self.grid_data = grid_data
        self.biome_id = biome_id
        self.terrain_color = terrain_color

        self.width_tiles = len(grid_data[0]) if grid_data else 0
        self.height_tiles = len(grid_data)

        self.obstacles: list[Obstacle] = []
        self._build_obstacles()

    def _build_obstacles(self) -> None:
        start_world_x = self.chunk_x * self.width_tiles * TILE_SIZE
        start_world_y = self.chunk_y * self.height_tiles * TILE_SIZE

        for y, row in enumerate(self.grid_data):
            for x, tile in enumerate(row):
                if tile == 1:
                    self.obstacles.append(
                        Obstacle(
                            start_world_x + x * TILE_SIZE,
                            start_world_y + y * TILE_SIZE,
                            TILE_SIZE,
                            TILE_SIZE,
                        )
                    )

    def render(self, surface: pygame.Surface, offset_x: int, offset_y: int) -> None:
        chunk_w = self.width_tiles * TILE_SIZE
        chunk_h = self.height_tiles * TILE_SIZE
        world_x = self.chunk_x * chunk_w
        world_y = self.chunk_y * chunk_h
        
        # Frustum culling check
        screen_width, screen_height = surface.get_size()
        if (world_x - offset_x > screen_width or 
            world_x + chunk_w - offset_x < 0 or
            world_y - offset_y > screen_height or
            world_y + chunk_h - offset_y < 0):
            return

        # Do not paint an opaque chunk-color background here.
        # The world background image is rendered in the environmental layer
        # and should stay visible behind obstacles/entities.
        for obs in self.obstacles:
            obs.render(surface, offset_x, offset_y)
