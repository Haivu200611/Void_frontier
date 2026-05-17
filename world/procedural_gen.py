from __future__ import annotations

import random


class MapGenerator:
    def __init__(self, width: int, height: int, seed: str | None = None):
        self.width = width
        self.height = height
        self._rng = random.Random(seed)

    def generate_caves(self, fill_prob: float = 0.45, iterations: int = 4) -> list[list[int]]:
        grid = [
            [1 if self._rng.random() < fill_prob else 0 for _ in range(self.width)]
            for _ in range(self.height)
        ]

        for _ in range(iterations):
            grid = self._smooth_step(grid)

        return grid

    def generate_flat(self) -> list[list[int]]:
        """Generates a completely empty/flat grid."""
        return [[0 for _ in range(self.width)] for _ in range(self.height)]

    def generate_flat_with_border(self, border_edges: set[str]) -> list[list[int]]:
        """Generates a flat grid with wall borders on specified edges."""
        grid = self.generate_flat()
        self._apply_border_walls(grid, border_edges)
        return grid

    def generate_caves_with_border(self, border_edges: set[str],
                                    fill_prob: float = 0.25,
                                    iterations: int = 4) -> list[list[int]]:
        """Generates caves with reduced obstacle density and wall borders."""
        grid = self.generate_caves(fill_prob=fill_prob, iterations=iterations)
        self._apply_border_walls(grid, border_edges)
        return grid

    def generate_void(self) -> list[list[int]]:
        """Generates a fully filled grid (impassable void)."""
        return [[1 for _ in range(self.width)] for _ in range(self.height)]

    def _apply_border_walls(self, grid: list[list[int]], border_edges: set[str],
                            thickness: int = 3) -> None:
        """Fill wall tiles along specified edges of the grid."""
        if "top" in border_edges:
            for y in range(thickness):
                for x in range(self.width):
                    grid[y][x] = 1
        if "bottom" in border_edges:
            for y in range(self.height - thickness, self.height):
                for x in range(self.width):
                    grid[y][x] = 1
        if "left" in border_edges:
            for y in range(self.height):
                for x in range(thickness):
                    grid[y][x] = 1
        if "right" in border_edges:
            for y in range(self.height):
                for x in range(self.width - thickness, self.width):
                    grid[y][x] = 1

    def _smooth_step(self, grid: list[list[int]]) -> list[list[int]]:
        new_grid = [[0 for _ in range(self.width)] for _ in range(self.height)]
        for y in range(self.height):
            for x in range(self.width):
                wall_count = self._count_walls(grid, x, y)
                if wall_count > 4:
                    new_grid[y][x] = 1
                elif wall_count < 4:
                    new_grid[y][x] = 0
                else:
                    new_grid[y][x] = grid[y][x]
        return new_grid

    def _count_walls(self, grid: list[list[int]], x: int, y: int) -> int:
        count = 0
        for ny in range(y - 1, y + 2):
            for nx in range(x - 1, x + 2):
                if nx == x and ny == y:
                    continue
                if nx < 0 or nx >= self.width or ny < 0 or ny >= self.height:
                    count += 1
                elif grid[ny][nx] == 1:
                    count += 1
        return count
