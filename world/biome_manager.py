from __future__ import annotations

import json
import os
import random
from typing import Iterable

from world.biome import Biome


class BiomeManager:
    """
    Deterministic, chunk-compatible biome assignment.
    Uses seeded region bands so the map scales without hardcoded layouts.
    """

    def __init__(self, seed: str, data_path: str = "data/biomes.json", region_size_chunks: int = 4):
        self.seed = seed
        self.region_size_chunks = max(1, int(region_size_chunks))
        self._biomes = self._load_biomes(data_path)
        self._cache: dict[tuple[int, int], Biome] = {}

    @property
    def biomes(self) -> tuple[Biome, ...]:
        return self._biomes

    def get_biome_for_chunk(self, chunk_x: int, chunk_y: int) -> Biome:
        key = (chunk_x, chunk_y)
        cached = self._cache.get(key)
        if cached:
            return cached

        region_x = chunk_x // self.region_size_chunks
        region_y = chunk_y // self.region_size_chunks
        rng = random.Random(f"{self.seed}:biome:{region_x}:{region_y}")
        biome = self._biomes[rng.randrange(0, len(self._biomes))]
        self._cache[key] = biome
        return biome

    def get_biome_id_for_chunk(self, chunk_x: int, chunk_y: int) -> str:
        return self.get_biome_for_chunk(chunk_x, chunk_y).biome_id

    def iter_cached(self) -> Iterable[tuple[tuple[int, int], Biome]]:
        return self._cache.items()

    @staticmethod
    def _load_biomes(data_path: str) -> tuple[Biome, ...]:
        if not os.path.exists(data_path):
            base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            data_path = os.path.join(base, data_path)

        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Biome data file not found: {data_path}")

        with open(data_path, "r", encoding="utf-8-sig") as f:
            raw = json.load(f)

        if not isinstance(raw, list) or not raw:
            raise ValueError("Biome data must be a non-empty list")

        biomes = tuple(Biome.from_dict(entry) for entry in raw)
        return biomes
