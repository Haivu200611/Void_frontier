"""
Utilities to load animation sequences from the assets folder.

This scans a folder structure like `assets/images/sprites/players/<action>/`
and builds `Animation` objects using `Frame` instances from
`rendering.animation_player`.
"""
import os
import re
from typing import Dict

from rendering.animation_player import Animation, Frame
from rendering.sprite_renderer import get_sprite_renderer


_NUM_RE = re.compile(r"(\d+)")


def _sort_files_numeric(files: list[str]) -> list[str]:
    def key_fn(name: str) -> int:
        m = _NUM_RE.search(name)
        return int(m.group(1)) if m else 0
    return sorted(files, key=key_fn)


def load_animations_from_folder(base_path: str = "assets/images/sprites/players",
                               frame_duration: float = 1.0 / 10.0) -> Dict[str, Animation]:
    """Load animations from subfolders under `base_path`.

    Each subfolder is treated as an action (e.g., `idle`, `walk`, `attack`).
    Files are sorted by the first numeric group in the filename (e.g. `idle_01.png`).

    Returns a dict mapping action name -> Animation instance.
    """
    sr = get_sprite_renderer()
    animations: Dict[str, Animation] = {}

    if not os.path.isdir(base_path):
        return animations

    for action in os.listdir(base_path):
        action_dir = os.path.join(base_path, action)
        if not os.path.isdir(action_dir):
            continue

        files = [
            f for f in os.listdir(action_dir)
            if os.path.isfile(os.path.join(action_dir, f))
            and f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
        ]
        files = _sort_files_numeric(files)
        frames: list[Frame] = []

        for f in files:
            rel_path = os.path.join("sprites/players", action, f).replace("\\", "/")
            # Use a unique cache key per file to avoid accidental collisions
            key = f"player_{action}_{f}"
            surf = sr.load_sprite(key, rel_path)
            frames.append(Frame(surf, frame_duration))

        if frames:
            animations[action] = Animation(action, frames, loop=True)

    return animations
