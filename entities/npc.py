import os
import re
from typing import List

import pygame

from entities.entity import Entity
from rendering.animation_player import Animation, AnimationPlayer, Frame
from rendering.sprite_renderer import SpriteRenderer
from settings import *


class NPC(Entity):
    def __init__(self, x, y, name="Trader", npc_type="trader", world_id: str | None = None):
        super().__init__(x, y, TILE_SIZE, TILE_SIZE, COLOR_NPC)
        self.name = name
        self.npc_type = npc_type
        self.world_id = world_id
        self.dialogue_index = 0
        self.dialogue = self._get_initial_dialogue()
        self.is_interactable = True

        self.talk_timer = 0.0
        self.talk_duration = 1.8

        self.sprite_renderer = SpriteRenderer()
        self.animation_player = AnimationPlayer()
        self._load_animations()
        if "idle" in self.animation_player.animations:
            self.animation_player.play("idle")

    def _get_initial_dialogue(self) -> List[str]:
        if self.npc_type == "scientist":
            return [
                "Data confirmed. The portal matrix is stable.",
                "Bring me 15 Meteor Ore and I will upgrade your equipment.",
                "Proceed to the next chapter when you are ready.",
            ]
        if self.npc_type == "survivor":
            return [
                "I made it through the toxic caves... barely.",
                "I can still trade upgrades for 15 Meteor Ore.",
                "Stay alert. The next region is worse.",
            ]
        if self.npc_type == "trader":
            return [
                "You made it to the ruins. Impressive.",
                "Bring me 3 Mystery Items, and I'll trade the Ship Repair Kit.",
                "No shortcuts in the Void Frontier.",
            ]
        return ["..."]

    _NUM_RE = re.compile(r"(\d+)")

    @classmethod
    def _sort_files_numeric(cls, files: list[str]) -> list[str]:
        def key_fn(name: str) -> int:
            m = cls._NUM_RE.search(name)
            return int(m.group(1)) if m else 0
        return sorted(files, key=key_fn)

    def _load_animations(self) -> None:
        base_dir = os.path.join("assets", "images", "npc", self.npc_type)
        actions = {"idle": "idle", "talk": "talk"}
        loaded_any = False

        for action_name, subdir in actions.items():
            action_dir = os.path.join(base_dir, subdir)
            if not os.path.isdir(action_dir):
                continue

            files = [
                f for f in os.listdir(action_dir)
                if os.path.isfile(os.path.join(action_dir, f))
                and f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
            ]
            files = self._sort_files_numeric(files)
            frames: list[Frame] = []
            for f in files:
                abs_path = os.path.abspath(os.path.join(action_dir, f))
                cache_key = f"npc_{self.npc_type}_{action_name}_{f}"
                surf = self.sprite_renderer.load_sprite(cache_key, abs_path)
                frames.append(Frame(surf, 1.0 / 24.0))

            if frames:
                self.animation_player.add_animation(Animation(action_name, frames, loop=True))
                loaded_any = True

        if not loaded_any:
            # Fallback static sprite if animation folders are missing.
            fallback = os.path.join(base_dir, "idle", "idle_01.png")
            self.sprite_renderer.load_sprite("npc_static", os.path.abspath(fallback))

    def set_talk(self, duration: float | None = None) -> None:
        self.talk_timer = duration if duration is not None else self.talk_duration

    def interact(self, progression_manager=None) -> str:
        # Update dialogue based on progression
        if progression_manager:
            self._update_dialogue(progression_manager)

        self.set_talk()
        current_text = self.dialogue[self.dialogue_index]
        self.dialogue_index = (self.dialogue_index + 1) % len(self.dialogue)
        return current_text

    def _update_dialogue(self, progression_manager):
        if self.npc_type == "trader":
            if progression_manager.check_endgame_ready():
                self.dialogue[1] = "You have everything. I'll trade the Ship Repair Kit now."
            elif len(progression_manager.collected_artifacts) > 0:
                self.dialogue[1] = (
                    f"You've found {len(progression_manager.collected_artifacts)} artifacts. "
                    "Bring me all 3 Mystery Items."
                )

    def update(self, dt: float) -> None:
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        super().update(dt)

        if self.talk_timer > 0:
            self.talk_timer = max(0.0, self.talk_timer - dt)

        if self.animation_player:
            if self.talk_timer > 0 and "talk" in self.animation_player.animations:
                self.animation_player.play("talk")
            elif "idle" in self.animation_player.animations:
                self.animation_player.play("idle")
            self.animation_player.update(dt)

    def render(self, surface: pygame.Surface, offset_x: int = 0, offset_y: int = 0) -> None:
        sprite = "npc_static"
        if self.animation_player and self.animation_player.get_current_sprite():
            sprite = self.animation_player.get_current_sprite()

        self.sprite_renderer.render_sprite_to_size(
            surface, sprite, self.x, self.y,
            self.width, self.height,
            offset_x, offset_y
        )

        # Name tag
        font = pygame.font.SysFont(None, 20)
        name_surf = font.render(self.name, True, (255, 255, 255))
        rect = self.rect.move(-offset_x, -offset_y)
        name_rect = name_surf.get_rect(midbottom=(rect.centerx, rect.top - 5))
        surface.blit(name_surf, name_rect)
