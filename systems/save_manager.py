from __future__ import annotations

import json
import os


class SaveManager:
    def __init__(self, save_dir: str = "saves"):
        self.save_dir = save_dir
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

    def save_game(
        self,
        slot: int,
        player,
        inventory,
        crafted_items: dict[str, int] | None = None,
        unlocked_portals: list[dict] | None = None,
        current_world: str | None = None,
        mined_ores: list[dict] | None = None,
        biome_states: dict | None = None,
        progression_flags: dict[str, bool] | None = None,
        status_effects: list[dict] | None = None,
        progression_data: dict | None = None,
    ) -> None:
        if hasattr(inventory, "to_save_data"):
            inventory_payload = inventory.to_save_data()
        else:
            inventory_payload = {
                "legacy_slots": {
                    str(k): {"id": v["item"].id, "count": v["count"]}
                    for k, v in inventory.items.items()
                }
            }

        data = {
            "player": {
                "x": player.x,
                "y": player.y,
                "health": player.health,
                "oxygen": player.oxygen,
                "hunger": player.hunger,
            },
            "inventory": inventory_payload,
            "crafted_items": crafted_items or {},
            "unlocked_portals": unlocked_portals or [],
            "current_world": current_world or "toxic_plains",
            "mined_ores": mined_ores or [],
            "biome_states": biome_states or {},
            "progression_flags": progression_flags or {},
            "status_effects": status_effects or [],
            "progression": progression_data or {},
        }

        with open(os.path.join(self.save_dir, f"save_{slot}.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_game(self, slot: int, player, inventory, all_items_db=None) -> dict | None:
        path = os.path.join(self.save_dir, f"save_{slot}.json")
        if not os.path.exists(path):
            return None

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        p_data = data.get("player", {})
        player.x = p_data.get("x", player.x)
        player.y = p_data.get("y", player.y)
        player.health = p_data.get("health", player.health)
        player.oxygen = p_data.get("oxygen", player.oxygen)
        player.hunger = p_data.get("hunger", player.hunger)

        inv_data = data.get("inventory", {})
        if hasattr(inventory, "load_save_data") and "slots" in inv_data:
            inventory.load_save_data(inv_data)
        elif all_items_db is not None and hasattr(inventory, "items"):
            inventory.items.clear()
            legacy = inv_data.get("legacy_slots", {})
            for k, v in legacy.items():
                item = all_items_db.get(v["id"])
                if item:
                    inventory.items[int(k)] = {"item": item, "count": v["count"]}

        # The progression data is returned to be loaded by ProgressionManager
        return data
