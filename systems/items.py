from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ItemData:
    id: str
    name: str
    description: str
    rarity: str
    stack_size: int
    value: int
    type: str
    consumable_effects: dict[str, float] = field(default_factory=dict)
    tool_stats: dict[str, float] = field(default_factory=dict)
    weapon_stats: dict[str, Any] = field(default_factory=dict)

    @property
    def max_stack(self) -> int:
        return self.stack_size


class ItemDatabase:
    _items: dict[str, ItemData] = {}
    _loaded_path: str | None = None

    @classmethod
    def load(cls, filepath: str = "data/items.json", force_reload: bool = False) -> None:
        resolved = cls._resolve_path(filepath)
        if not force_reload and cls._items and cls._loaded_path == resolved:
            return

        if not os.path.exists(resolved):
            raise FileNotFoundError(f"Item data not found at {resolved}")

        with open(resolved, "r", encoding="utf-8-sig") as f:
            raw = json.load(f)

        cls._items.clear()
        iterable: list[tuple[str, dict[str, Any]]]
        if isinstance(raw, dict):
            iterable = list(raw.items())
        elif isinstance(raw, list):
            iterable = [(entry.get("id", f"item_{idx}"), entry) for idx, entry in enumerate(raw)]
        else:
            raise ValueError("items.json must be an object or a list")

        for item_id, payload in iterable:
            stack_size = int(payload.get("stack_size", payload.get("max_stack", 64)))
            cls._items[item_id] = ItemData(
                id=payload.get("id", item_id),
                name=payload.get("name", item_id),
                description=payload.get("description", ""),
                rarity=payload.get("rarity", "Common"),
                stack_size=max(1, stack_size),
                value=int(payload.get("value", 0)),
                type=payload.get("type", "material"),
                consumable_effects=dict(payload.get("consumable_effects", {})),
                tool_stats=dict(payload.get("tool_stats", {})),
                weapon_stats=dict(payload.get("weapon_stats", {})),
            )

        cls._loaded_path = resolved

    @classmethod
    def ensure_loaded(cls) -> None:
        if not cls._items:
            cls.load()

    @classmethod
    def get_item(cls, item_id: str) -> ItemData | None:
        cls.ensure_loaded()
        return cls._items.get(item_id)

    @classmethod
    def all_items(cls) -> dict[str, ItemData]:
        cls.ensure_loaded()
        return dict(cls._items)

    @classmethod
    def get_items_by_type(cls, item_type: str) -> list[ItemData]:
        cls.ensure_loaded()
        return [item for item in cls._items.values() if item.type == item_type]

    @staticmethod
    def _resolve_path(path: str) -> str:
        if os.path.exists(path):
            return path
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        alt = os.path.join(base, path)
        return alt
