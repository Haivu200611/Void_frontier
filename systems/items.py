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
    icon_path: str = ""
    display_size: tuple[int, int] = (32, 32)  # Width, Height for rendering

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

        # Scan images
        image_map = {}
        images_base = cls._resolve_path(os.path.join("assets", "images"))
        items_dir = os.path.join(images_base, "items")
        if os.path.exists(items_dir):
            for root, dirs, files in os.walk(items_dir):
                for file in files:
                    if file.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                        clean_name = os.path.splitext(file)[0].strip().lower()
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, images_base)
                        # Normalize path separators for consistency
                        image_map[clean_name] = rel_path.replace("\\", "/")

        for item_id, payload in iterable:
            stack_size = int(payload.get("stack_size", payload.get("max_stack", 64)))
            
            name = payload.get("name", item_id)
            clean_name = name.strip().lower()
            icon_path = image_map.get(clean_name, "")
            
            # Parse display_size from JSON
            display_size_raw = payload.get("display_size", [32, 32])
            if isinstance(display_size_raw, (list, tuple)) and len(display_size_raw) >= 2:
                display_size = (int(display_size_raw[0]), int(display_size_raw[1]))
            else:
                display_size = (32, 32)
            
            cls._items[item_id] = ItemData(
                id=payload.get("id", item_id),
                name=name,
                description=payload.get("description", ""),
                rarity=payload.get("rarity", "Common"),
                stack_size=max(1, stack_size),
                value=int(payload.get("value", 0)),
                type=payload.get("type", "material"),
                consumable_effects=dict(payload.get("consumable_effects", {})),
                tool_stats=dict(payload.get("tool_stats", {})),
                weapon_stats=dict(payload.get("weapon_stats", {})),
                icon_path=icon_path,
                display_size=display_size,
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
