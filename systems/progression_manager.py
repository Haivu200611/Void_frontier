"""
Progression Manager
Handles world unlocks, boss flags, and artifact tracking
"""
import json
import os
from typing import Dict, List, Set, Optional

class ProgressionManager:
    def __init__(self, data_path: str = "data/progression.json"):
        self.data_path = data_path
        self.progression_data = self._load_data()
        
        # Current state
        self.unlocked_worlds: Set[str] = {"toxic_plains"}
        self.defeated_bosses: Set[str] = set()
        self.collected_artifacts: Set[str] = set()
        self.has_ship_repair_kit: bool = False
        self.current_world_index: int = 1
        
    def _load_data(self) -> Dict:
        if os.path.exists(self.data_path):
            with open(self.data_path, 'r') as f:
                return json.load(f)
        return {}

    def can_unlock_world(self, world_id: str) -> bool:
        """Check if the requirements for a world are met"""
        world_info = self.progression_data["worlds"].get(world_id)
        if not world_info:
            return False
            
        req = world_info["unlock_requirement"]
        if req is None:
            return True
            
        # Check if requirement is in artifacts or special items
        return req in self.collected_artifacts or req == "battery_core"

    def unlock_world(self, world_id: str) -> bool:
        """Unlock a world if requirements are met"""
        if self.can_unlock_world(world_id):
            self.unlocked_worlds.add(world_id)
            return True
        return False

    def mark_boss_defeated(self, boss_id: str) -> str:
        """Mark boss as defeated and return reward"""
        self.defeated_bosses.add(boss_id)
        
        # Find reward from data
        for world_id, info in self.progression_data["worlds"].items():
            if info["boss"] == boss_id:
                return info["reward"]
        return None

    def add_artifact(self, artifact_id: str) -> None:
        """Add artifact to collection"""
        self.collected_artifacts.add(artifact_id)

    def check_endgame_ready(self) -> bool:
        """Check if all artifacts are collected"""
        required = set(self.progression_data["endgame"]["required_artifacts"])
        return required.issubset(self.collected_artifacts)

    def get_current_objective(self) -> str:
        """Get a human-readable objective based on progression"""
        if not self.progression_data["worlds"]: return "Explore the world"
        
        # Find the first locked world
        for world_id, info in self.progression_data["worlds"].items():
            if world_id not in self.unlocked_worlds:
                req = info["unlock_requirement"]
                return f"Find {req} to unlock {world_id}"
            
            # If world is unlocked but boss not defeated
            if info["boss"] not in self.defeated_bosses:
                return f"Defeat {info['boss']} in {world_id}"
        
        if not self.check_endgame_ready():
            return "Collect all 3 Artifacts"
            
        return "Return to Fallen Planet and repair ORION-7"

    def save_progression(self, save_data: Dict) -> None:
        """Save progression state into game save"""
        save_data["progression"] = {
            "unlocked_worlds": list(self.unlocked_worlds),
            "defeated_bosses": list(self.defeated_bosses),
            "collected_artifacts": list(self.collected_artifacts),
            "has_ship_repair_kit": self.has_ship_repair_kit
        }

    def load_progression(self, save_data: Dict) -> None:
        """Load progression state from save"""
        prog = save_data.get("progression", {})
        self.unlocked_worlds = set(prog.get("unlocked_worlds", ["toxic_plains"]))
        self.defeated_bosses = set(prog.get("defeated_bosses", []))
        self.collected_artifacts = set(prog.get("collected_artifacts", []))
        self.has_ship_repair_kit = prog.get("has_ship_repair_kit", False)
