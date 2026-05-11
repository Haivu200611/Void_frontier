from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from systems.items import ItemData, ItemDatabase


@dataclass
class ItemStack:
    item_id: str
    count: int
    durability: int | None = None


@dataclass
class DragPayload:
    source: Literal["inventory", "equipment"]
    source_index: int | str
    stack: ItemStack


class Inventory:
    def __init__(self, grid_cols: int = 8, grid_rows: int = 3, hotbar_size: int = 9):
        self.grid_cols = grid_cols
        self.grid_rows = grid_rows
        self.slot_count = grid_cols * grid_rows

        self.slots: list[ItemStack | None] = [None] * self.slot_count
        self.hotbar_size = max(1, min(hotbar_size, self.slot_count))
        self.selected_hotbar = 0

        self.equipment: dict[str, ItemStack | None] = {
            "tool": None,
            "weapon": None,
            "armor": None,
            "gadget": None,
        }

        self.drag_payload: DragPayload | None = None

    # ------------------------------------------------------------------
    # Core item operations
    # ------------------------------------------------------------------

    def add_item(self, item_or_id: ItemData | str, count: int = 1, durability: int | None = None) -> int:
        """Add item and return leftover count that could not fit."""
        item = self._resolve_item(item_or_id)
        if item is None or count <= 0:
            return count

        remaining = count
        # Merge with existing stacks first.
        for idx, slot in enumerate(self.slots):
            if remaining <= 0:
                break
            if slot is None or slot.item_id != item.id:
                continue
            if self._is_non_stackable_tool(slot.item_id):
                continue

            space = item.stack_size - slot.count
            if space <= 0:
                continue
            moved = min(space, remaining)
            slot.count += moved
            remaining -= moved

        # Fill empty slots.
        while remaining > 0:
            free = self._first_free_slot()
            if free is None:
                break
            moved = min(item.stack_size, remaining)
            stack_durability = durability
            if item.type == "tool" and stack_durability is None:
                stack_durability = int(item.tool_stats.get("durability", 0))
            self.slots[free] = ItemStack(item_id=item.id, count=moved, durability=stack_durability)
            remaining -= moved

        return remaining

    def remove_item(self, item_id: str, count: int = 1) -> bool:
        if count <= 0:
            return True

        needed = count
        for slot in self.slots:
            if slot is None or slot.item_id != item_id:
                continue
            taken = min(slot.count, needed)
            slot.count -= taken
            needed -= taken
            if slot.count <= 0:
                self._clear_slot_reference(slot)
            if needed <= 0:
                return True

        for key, equip in self.equipment.items():
            if needed <= 0:
                break
            if equip is None or equip.item_id != item_id:
                continue
            taken = min(equip.count, needed)
            equip.count -= taken
            needed -= taken
            if equip.count <= 0:
                self.equipment[key] = None

        return needed <= 0

    def count_item(self, item_id: str) -> int:
        total = 0
        for slot in self.slots:
            if slot and slot.item_id == item_id:
                total += slot.count
        for equip in self.equipment.values():
            if equip and equip.item_id == item_id:
                total += equip.count
        return total

    def get_occupied_slot_count(self) -> int:
        """Count non-empty slots in the grid."""
        return sum(1 for slot in self.slots if slot is not None)

    def is_full(self) -> bool:
        """Check if all grid slots are occupied."""
        return self.get_occupied_slot_count() >= self.slot_count

    def has_items(self, requirements: dict[str, int]) -> bool:
        return all(self.count_item(item_id) >= count for item_id, count in requirements.items())

    # ------------------------------------------------------------------
    # Grid / hotbar / drag-drop
    # ------------------------------------------------------------------

    def set_selected_hotbar(self, index: int) -> None:
        self.selected_hotbar = max(0, min(self.hotbar_size - 1, index))

    def cycle_hotbar(self, delta: int) -> None:
        self.selected_hotbar = (self.selected_hotbar + delta) % self.hotbar_size

    def get_hotbar_slot(self, index: int | None = None) -> ItemStack | None:
        idx = self.selected_hotbar if index is None else max(0, min(self.hotbar_size - 1, index))
        return self.slots[idx]

    def consume_selected_hotbar_item(self, amount: int = 1) -> str | None:
        slot = self.get_hotbar_slot()
        if slot is None or slot.count < amount:
            return None
        item_id = slot.item_id
        slot.count -= amount
        if slot.count <= 0:
            self.slots[self.selected_hotbar] = None
        return item_id

    def move_stack(self, src_index: int, dst_index: int) -> bool:
        if not self._valid_index(src_index) or not self._valid_index(dst_index) or src_index == dst_index:
            return False

        src = self.slots[src_index]
        if src is None:
            return False

        dst = self.slots[dst_index]
        if dst is None:
            self.slots[dst_index] = src
            self.slots[src_index] = None
            return True

        if dst.item_id == src.item_id and not self._is_non_stackable_tool(src.item_id):
            item = ItemDatabase.get_item(src.item_id)
            if item is None:
                return False
            space = item.stack_size - dst.count
            if space > 0:
                moved = min(space, src.count)
                dst.count += moved
                src.count -= moved
                if src.count <= 0:
                    self.slots[src_index] = None
                return True

        self.slots[src_index], self.slots[dst_index] = self.slots[dst_index], self.slots[src_index]
        return True

    def split_stack(self, src_index: int, dst_index: int, amount: int) -> bool:
        if not self._valid_index(src_index) or not self._valid_index(dst_index):
            return False
        src = self.slots[src_index]
        dst = self.slots[dst_index]
        if src is None or amount <= 0 or src.count <= amount or dst is not None:
            return False

        src.count -= amount
        self.slots[dst_index] = ItemStack(item_id=src.item_id, count=amount, durability=src.durability)
        return True

    def begin_drag(self, source: Literal["inventory", "equipment"], source_index: int | str) -> bool:
        if source == "inventory":
            if not isinstance(source_index, int) or not self._valid_index(source_index):
                return False
            stack = self.slots[source_index]
            if stack is None:
                return False
            self.drag_payload = DragPayload(source=source, source_index=source_index, stack=stack)
            self.slots[source_index] = None
            return True

        if source == "equipment":
            if not isinstance(source_index, str) or source_index not in self.equipment:
                return False
            stack = self.equipment[source_index]
            if stack is None:
                return False
            self.drag_payload = DragPayload(source=source, source_index=source_index, stack=stack)
            self.equipment[source_index] = None
            return True

        return False

    def drop_drag(self, destination: Literal["inventory", "equipment"], destination_index: int | str) -> bool:
        if self.drag_payload is None:
            return False

        payload = self.drag_payload
        self.drag_payload = None

        if destination == "inventory" and isinstance(destination_index, int) and self._valid_index(destination_index):
            existing = self.slots[destination_index]
            if existing is None:
                self.slots[destination_index] = payload.stack
                return True

            if existing.item_id == payload.stack.item_id and not self._is_non_stackable_tool(payload.stack.item_id):
                item = ItemDatabase.get_item(existing.item_id)
                if item:
                    space = item.stack_size - existing.count
                    moved = min(space, payload.stack.count)
                    existing.count += moved
                    payload.stack.count -= moved
                    if payload.stack.count <= 0:
                        return True

            # swap fallback
            self.slots[destination_index] = payload.stack
            self._restore_payload(existing, payload)
            return True

        if destination == "equipment" and isinstance(destination_index, str) and destination_index in self.equipment:
            if not self._can_equip(payload.stack.item_id, destination_index):
                self._restore_payload(payload.stack, payload)
                return False
            existing = self.equipment[destination_index]
            self.equipment[destination_index] = payload.stack
            if existing:
                self._restore_payload(existing, payload)
            return True

        self._restore_payload(payload.stack, payload)
        return False

    def equip_from_slot(self, slot_index: int, equip_slot: str = "tool") -> bool:
        if not self._valid_index(slot_index) or equip_slot not in self.equipment:
            return False
        stack = self.slots[slot_index]
        if stack is None or not self._can_equip(stack.item_id, equip_slot):
            return False

        previous = self.equipment[equip_slot]
        self.equipment[equip_slot] = stack
        self.slots[slot_index] = previous
        return True

    def unequip_to_inventory(self, equip_slot: str) -> bool:
        if equip_slot not in self.equipment or self.equipment[equip_slot] is None:
            return False
        stack = self.equipment[equip_slot]
        self.equipment[equip_slot] = None
        if stack is None:
            return False

        leftover = self.add_item(stack.item_id, stack.count, durability=stack.durability)
        if leftover > 0:
            stack.count = leftover
            self.equipment[equip_slot] = stack
            return False
        return True

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_item_data(self, stack: ItemStack | None) -> ItemData | None:
        if stack is None:
            return None
        return ItemDatabase.get_item(stack.item_id)

    def get_active_tool_stack(self) -> ItemStack | None:
        equipped = self.equipment.get("tool")
        if equipped:
            return equipped

        slot = self.get_hotbar_slot()
        if slot is None:
            return None
        item = ItemDatabase.get_item(slot.item_id)
        if item and item.type == "tool":
            return slot
        return None

    # ------------------------------------------------------------------
    # Save / load
    # ------------------------------------------------------------------

    def to_save_data(self) -> dict:
        return {
            "slots": [self._stack_to_dict(slot) for slot in self.slots],
            "hotbar_size": self.hotbar_size,
            "selected_hotbar": self.selected_hotbar,
            "equipment": {key: self._stack_to_dict(value) for key, value in self.equipment.items()},
        }

    def load_save_data(self, data: dict) -> None:
        slots_payload = data.get("slots", [])
        self.slots = [self._stack_from_dict(entry) for entry in slots_payload[: self.slot_count]]
        while len(self.slots) < self.slot_count:
            self.slots.append(None)

        self.hotbar_size = max(1, min(int(data.get("hotbar_size", self.hotbar_size)), self.slot_count))
        self.selected_hotbar = max(0, min(int(data.get("selected_hotbar", 0)), self.hotbar_size - 1))

        equipment_payload = data.get("equipment", {})
        for key in self.equipment:
            self.equipment[key] = self._stack_from_dict(equipment_payload.get(key))

        self.drag_payload = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_item(self, item_or_id: ItemData | str) -> ItemData | None:
        if isinstance(item_or_id, ItemData):
            return item_or_id
        return ItemDatabase.get_item(item_or_id)

    def _first_free_slot(self) -> int | None:
        for idx, slot in enumerate(self.slots):
            if slot is None:
                return idx
        return None

    def _valid_index(self, index: int) -> bool:
        return 0 <= index < self.slot_count

    @staticmethod
    def _stack_to_dict(stack: ItemStack | None) -> dict | None:
        if stack is None:
            return None
        return {
            "item_id": stack.item_id,
            "count": stack.count,
            "durability": stack.durability,
        }

    @staticmethod
    def _stack_from_dict(payload: dict | None) -> ItemStack | None:
        if not payload:
            return None
        return ItemStack(
            item_id=str(payload.get("item_id", "")),
            count=int(payload.get("count", 0)),
            durability=payload.get("durability"),
        )

    def _restore_payload(self, stack: ItemStack, payload: DragPayload) -> None:
        if payload.source == "inventory" and isinstance(payload.source_index, int) and self._valid_index(payload.source_index):
            if self.slots[payload.source_index] is None:
                self.slots[payload.source_index] = stack
                return
        if payload.source == "equipment" and isinstance(payload.source_index, str) and payload.source_index in self.equipment:
            if self.equipment[payload.source_index] is None:
                self.equipment[payload.source_index] = stack
                return

        free = self._first_free_slot()
        if free is not None:
            self.slots[free] = stack

    def _is_non_stackable_tool(self, item_id: str) -> bool:
        item = ItemDatabase.get_item(item_id)
        if item is None:
            return False
        return item.type == "tool" or item.stack_size <= 1

    def _can_equip(self, item_id: str, equip_slot: str) -> bool:
        item = ItemDatabase.get_item(item_id)
        if item is None:
            return False
        if equip_slot == "tool":
            return item.type == "tool"
        if equip_slot == "weapon":
            return item.type in {"weapon", "ammo"}
        if equip_slot == "armor":
            return item.type in {"armor", "upgrade"}
        if equip_slot == "gadget":
            return item.type in {"upgrade", "quest_item"}
        return False

    def _clear_slot_reference(self, slot_ref: ItemStack) -> None:
        for idx, slot in enumerate(self.slots):
            if slot is slot_ref:
                self.slots[idx] = None
                return
