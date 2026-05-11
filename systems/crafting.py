from __future__ import annotations

import json
import os
from dataclasses import dataclass

from systems.items import ItemDatabase


@dataclass(frozen=True)
class Recipe:
    recipe_id: str
    name: str
    category: str
    result_item_id: str
    result_count: int
    ingredients: dict[str, int]


class CraftingManager:
    def __init__(self, filepath: str = "data/crafting_recipes.json"):
        self.filepath = self._resolve_path(filepath)
        self.recipes: list[Recipe] = []
        self.crafted_history: dict[str, int] = {}
        self.load_recipes()

    def load_recipes(self) -> None:
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"Crafting recipe file not found: {self.filepath}")

        with open(self.filepath, "r", encoding="utf-8-sig") as f:
            raw = json.load(f)

        if not isinstance(raw, list):
            raise ValueError("crafting_recipes.json must be a list")

        self.recipes.clear()
        for entry in raw:
            result = entry.get("result", {})
            recipe = Recipe(
                recipe_id=entry.get("id", "unknown_recipe"),
                name=entry.get("name", entry.get("id", "Recipe")),
                category=entry.get("category", "misc"),
                result_item_id=result.get("item_id", ""),
                result_count=int(result.get("count", 1)),
                ingredients={k: int(v) for k, v in entry.get("ingredients", {}).items()},
            )
            self.recipes.append(recipe)

    def get_recipes_by_category(self, category: str) -> list[Recipe]:
        return [recipe for recipe in self.recipes if recipe.category == category]

    def get_recipe(self, recipe_ref: str | int) -> Recipe | None:
        if isinstance(recipe_ref, int):
            if 0 <= recipe_ref < len(self.recipes):
                return self.recipes[recipe_ref]
            return None
        for recipe in self.recipes:
            if recipe.recipe_id == recipe_ref:
                return recipe
        return None

    def can_craft(self, recipe_ref: str | int, inventory) -> bool:
        recipe = self.get_recipe(recipe_ref)
        if recipe is None:
            return False
        return inventory.has_items(recipe.ingredients)

    def craft(self, recipe_ref: str | int, inventory) -> tuple[bool, str]:
        recipe = self.get_recipe(recipe_ref)
        if recipe is None:
            return False, "Invalid recipe"

        if not self.can_craft(recipe_ref, inventory):
            return False, "Missing materials"

        for item_id, count in recipe.ingredients.items():
            inventory.remove_item(item_id, count)

        result_item = ItemDatabase.get_item(recipe.result_item_id)
        if result_item is None:
            return False, "Result item not found"

        leftover = inventory.add_item(result_item, recipe.result_count)
        crafted_count = recipe.result_count - leftover
        if crafted_count <= 0:
            # inventory full, rollback consumed materials
            for item_id, count in recipe.ingredients.items():
                inventory.add_item(item_id, count)
            return False, "Inventory full"

        self.crafted_history[recipe.recipe_id] = self.crafted_history.get(recipe.recipe_id, 0) + crafted_count
        return True, recipe.recipe_id

    def to_save_data(self) -> dict[str, int]:
        return dict(self.crafted_history)

    def load_save_data(self, payload: dict[str, int]) -> None:
        self.crafted_history = {str(k): int(v) for k, v in payload.items()}

    @staticmethod
    def _resolve_path(path: str) -> str:
        if os.path.exists(path):
            return path
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        return os.path.join(base, path)
