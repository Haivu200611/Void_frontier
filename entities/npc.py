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

    def render(self, surface: pygame.Surface, offset_x: int = 0, offset_y: int = 0) -> None:
        if not hasattr(self, 'sprite_renderer'):
            from rendering.sprite_renderer import SpriteRenderer
            self.sprite_renderer = SpriteRenderer()
            npc_img = {
                "trader": "npc/trader.png",
                "scientist": "npc/scientist.png",
                "survivor": "npc/survivor.png"
            }.get(self.npc_type, "npc/trader.png")
            self.sprite_renderer.load_sprite("npc", npc_img)
            
        self.sprite_renderer.render_sprite(
            surface, "npc", self.x, self.y,
            offset_x, offset_y, scale=1.5
        )
        
        # Name tag
        font = pygame.font.SysFont(None, 20)
        name_surf = font.render(self.name, True, (255, 255, 255))
        rect = self.rect.move(-offset_x, -offset_y)
        name_rect = name_surf.get_rect(midbottom=(rect.centerx, rect.top - 5))
        surface.blit(name_surf, name_rect)

