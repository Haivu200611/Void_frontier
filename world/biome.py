from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AmbientSettings:
    fog_color: tuple[int, int, int]
    fog_strength: float


@dataclass(frozen=True)
class Biome:
    biome_id: str
    name: str
    terrain_color: tuple[int, int, int]
    enemy_types: tuple[str, ...]
    ore_types: tuple[str, ...]
    ambient: AmbientSettings
    hazard_types: tuple[str, ...]
    resource_spawn_modifier: float = 1.0

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Biome":
        ambient_data = payload.get("ambient", {})
        fog = ambient_data.get("fog_color", [60, 60, 70])
        biome_id = payload.get("id", "unknown_biome")
        return cls(
            biome_id=biome_id,
            name=payload.get("name", biome_id.replace("_", " ").title()),
            terrain_color=tuple(payload.get("terrain_color", [40, 40, 46])),
            enemy_types=tuple(payload.get("enemy_types", ["dummy_enemy"])),
            ore_types=tuple(payload.get("ore_types", [])),
            ambient=AmbientSettings(
                fog_color=(int(fog[0]), int(fog[1]), int(fog[2])),
                fog_strength=float(ambient_data.get("fog_strength", 0.0)),
            ),
            hazard_types=tuple(payload.get("hazard_types", [])),
            resource_spawn_modifier=float(payload.get("resource_spawn_modifier", 1.0)),
        )
