from __future__ import annotations

import random
from dataclasses import dataclass

import pygame

from entities.item_drop import ResourceDrop
from systems.items import ItemDatabase


@dataclass
class MiningToolStats:
    mining_speed: float = 1.0
    mining_power: int = 1
    cooldown: float = 0.45
    efficiency: float = 1.0


class MiningSystem:
    def __init__(self):
        self.mining_range = 120.0
        self.base_cooldown = 0.45
        self.base_damage = 36.0
        self.cooldown_timer = 0.0
        self.last_feedback: str = ""
        self.feedback_timer = 0.0

    def update(self, dt: float) -> None:
        if self.cooldown_timer > 0:
            self.cooldown_timer = max(0.0, self.cooldown_timer - dt)
        if self.feedback_timer > 0:
            self.feedback_timer = max(0.0, self.feedback_timer - dt)

    def try_mine(self, player, ores: list, item_drops: list, camera, mine_input: bool) -> bool:
        if not mine_input or self.cooldown_timer > 0:
            return False

        tool_stack = player.inventory.get_active_tool_stack() if hasattr(player, "inventory") else None
        stats = self._resolve_tool_stats(tool_stack.item_id if tool_stack else None)

        mouse_x, mouse_y = pygame.mouse.get_pos()
        world_mouse_x, world_mouse_y = camera.screen_to_world(mouse_x, mouse_y)
        target = self._find_target_ore(player, ores, world_mouse_x, world_mouse_y)
        if target is None:
            self._set_feedback("No ore in range")
            return False

        # Design rule: hardness 2 ores can only be mined by Crystal Pickaxe.
        if target.hardness == 2 and (tool_stack is None or tool_stack.item_id != "tool_crystal_pickaxe"):
            self.cooldown_timer = max(0.08, stats.cooldown)
            self._set_feedback("Crystal Pickaxe required")
            return False

        damage = self.base_damage * stats.mining_speed * stats.efficiency
        mined = target.take_mining_damage(damage, stats.mining_power)
        self.cooldown_timer = max(0.08, stats.cooldown)

        if not mined:
            self._set_feedback("Tool power too low")
            return False

        self._consume_tool_durability(player, tool_stack)

        if target.is_dead:
            amount = random.randint(target.drop_amount[0], target.drop_amount[1])
            item_drops.append(ResourceDrop(target.x, target.y, target.drop_id, amount))
            self._set_feedback(f"Mined {target.ore_type} +{amount}")
        else:
            self._set_feedback(f"Mining {target.ore_type}...")

        return True

    def _find_target_ore(self, player, ores: list, wx: float, wy: float):
        mouse_rect = pygame.Rect(int(wx - 4), int(wy - 4), 8, 8)
        nearest = None
        nearest_dist = 10_000.0

        for ore in ores:
            if ore.is_dead:
                continue
            if not ore.hitbox.rect.colliderect(mouse_rect):
                continue
            dist = ((player.x - ore.x) ** 2 + (player.y - ore.y) ** 2) ** 0.5
            if dist <= self.mining_range and dist < nearest_dist:
                nearest = ore
                nearest_dist = dist

        return nearest

    def _resolve_tool_stats(self, item_id: str | None) -> MiningToolStats:
        if not item_id:
            return MiningToolStats(cooldown=self.base_cooldown)

        item = ItemDatabase.get_item(item_id)
        if item is None or item.type != "tool":
            return MiningToolStats(cooldown=self.base_cooldown)

        stats = item.tool_stats
        return MiningToolStats(
            mining_speed=float(stats.get("mining_speed", 1.0)),
            mining_power=int(stats.get("mining_power", 1)),
            cooldown=float(stats.get("cooldown", self.base_cooldown)),
            efficiency=float(stats.get("efficiency", 1.0)),
        )

    def _consume_tool_durability(self, player, tool_stack) -> None:
        if tool_stack is None:
            return
        item = ItemDatabase.get_item(tool_stack.item_id)
        if item is None or item.type != "tool":
            return

        max_durability = int(item.tool_stats.get("durability", 0))
        if max_durability <= 0:
            return

        if tool_stack.durability is None:
            tool_stack.durability = max_durability

        tool_stack.durability -= 1
        if tool_stack.durability > 0:
            return

        # Tool breaks.
        tool_stack.count -= 1
        self._set_feedback(f"{item.name} broke")
        if tool_stack.count <= 0:
            equipped = player.inventory.equipment.get("tool")
            if equipped is tool_stack:
                player.inventory.equipment["tool"] = None
            else:
                for idx, slot in enumerate(player.inventory.slots):
                    if slot is tool_stack:
                        player.inventory.slots[idx] = None
                        break

    def _set_feedback(self, text: str, duration: float = 0.75) -> None:
        self.last_feedback = text
        self.feedback_timer = duration

    def get_feedback(self) -> str:
        if self.feedback_timer <= 0:
            return ""
        return self.last_feedback
