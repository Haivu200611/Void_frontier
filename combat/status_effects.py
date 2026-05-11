from __future__ import annotations

from dataclasses import dataclass

import pygame


@dataclass
class EffectTemplate:
    effect_id: str
    duration: float
    tick_interval: float
    tick_damage: float
    max_stacks: int
    speed_multiplier: float = 1.0
    color: tuple[int, int, int] = (255, 255, 255)


@dataclass
class ActiveEffect:
    template: EffectTemplate
    remaining: float
    time_until_tick: float
    stacks: int = 1


EFFECT_LIBRARY: dict[str, EffectTemplate] = {
    "poison": EffectTemplate("poison", duration=6.0, tick_interval=1.0, tick_damage=4.0, max_stacks=3, color=(110, 255, 120)),
    "burn": EffectTemplate("burn", duration=4.0, tick_interval=0.5, tick_damage=6.0, max_stacks=2, color=(255, 120, 40)),
    "slow": EffectTemplate("slow", duration=3.5, tick_interval=0.0, tick_damage=0.0, max_stacks=1, speed_multiplier=0.7, color=(120, 170, 255)),
    "toxic_damage": EffectTemplate("toxic_damage", duration=5.0, tick_interval=1.0, tick_damage=5.0, max_stacks=4, color=(150, 255, 80)),
}


class StatusEffectManager:
    def __init__(self):
        self.active_effects: dict[str, ActiveEffect] = {}

    def apply_effect(self, effect_id: str) -> None:
        template = EFFECT_LIBRARY.get(effect_id)
        if not template:
            return

        existing = self.active_effects.get(effect_id)
        if existing is None:
            self.active_effects[effect_id] = ActiveEffect(
                template=template,
                remaining=template.duration,
                time_until_tick=template.tick_interval,
                stacks=1,
            )
            return

        existing.remaining = max(existing.remaining, template.duration)
        existing.stacks = min(template.max_stacks, existing.stacks + 1)

    def update(self, dt: float, entity) -> None:
        remove: list[str] = []
        for effect_id, active in self.active_effects.items():
            active.remaining -= dt

            if active.template.tick_interval > 0:
                active.time_until_tick -= dt
                while active.time_until_tick <= 0 and active.remaining > 0:
                    dmg = active.template.tick_damage * active.stacks
                    if dmg > 0:
                        entity.health = max(0.0, entity.health - dmg)
                        if entity.health <= 0:
                            entity.is_dead = True
                    active.time_until_tick += active.template.tick_interval

            if active.remaining <= 0:
                remove.append(effect_id)

        for effect_id in remove:
            self.active_effects.pop(effect_id, None)

    def get_speed_multiplier(self) -> float:
        mult = 1.0
        for active in self.active_effects.values():
            mult *= active.template.speed_multiplier
        return max(0.45, mult)

    def has_effect(self, effect_id: str) -> bool:
        return effect_id in self.active_effects

    def debug_lines(self) -> list[str]:
        lines: list[str] = []
        for effect_id, active in self.active_effects.items():
            lines.append(f"{effect_id} x{active.stacks} ({active.remaining:.1f}s)")
        return lines

    def render_debug(self, surface: pygame.Surface, font: pygame.font.Font, x: int, y: int) -> None:
        for idx, line in enumerate(self.debug_lines()):
            txt = font.render(line, True, (240, 240, 180))
            surface.blit(txt, (x, y + idx * 16))

    def to_save_data(self) -> list[dict]:
        return [
            {
                "effect_id": key,
                "remaining": value.remaining,
                "time_until_tick": value.time_until_tick,
                "stacks": value.stacks,
            }
            for key, value in self.active_effects.items()
        ]

    def load_save_data(self, entries: list[dict]) -> None:
        self.active_effects.clear()
        for entry in entries:
            effect_id = entry.get("effect_id")
            template = EFFECT_LIBRARY.get(effect_id)
            if not template:
                continue
            self.active_effects[effect_id] = ActiveEffect(
                template=template,
                remaining=float(entry.get("remaining", template.duration)),
                time_until_tick=float(entry.get("time_until_tick", template.tick_interval)),
                stacks=int(entry.get("stacks", 1)),
            )
