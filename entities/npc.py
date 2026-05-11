from entities.entity import Entity
from settings import *
from typing import List

class NPC(Entity):
    def __init__(self, x, y, name="Trader", npc_type="trader"):
        super().__init__(x, y, TILE_SIZE, TILE_SIZE, COLOR_NPC)
        self.name = name
        self.npc_type = npc_type
        self.dialogue_index = 0
        self.dialogue = self._get_initial_dialogue()
        self.is_interactable = True
        
    def _get_initial_dialogue(self) -> List[str]:
        if self.npc_type == "trader":
            return [
                "Hello traveler. I deal in rare artifacts.",
                "If you bring me all three artifacts, I can give you the Ship Repair Kit.",
                "Good luck in the Void."
            ]
        elif self.npc_type == "guide":
            return [
                "Welcome to the frontier.",
                "The portals are locked by ancient cores.",
                "Defeat the boss of each world to progress."
            ]
        return ["..."]

    def interact(self, progression_manager=None):
        # Update dialogue based on progression
        if progression_manager:
            self._update_dialogue(progression_manager)
        
        current_text = self.dialogue[self.dialogue_index]
        print(f"[{self.name}]: {current_text}")
        
        self.dialogue_index = (self.dialogue_index + 1) % len(self.dialogue)

    def _update_dialogue(self, progression_manager):
        if self.npc_type == "trader":
            if progression_manager.check_endgame_ready():
                self.dialogue[1] = "You have the artifacts! I can give you the Ship Repair Kit now."
            elif len(progression_manager.collected_artifacts) > 0:
                self.dialogue[1] = f"You've found {len(progression_manager.collected_artifacts)} artifacts. Keep searching!"

