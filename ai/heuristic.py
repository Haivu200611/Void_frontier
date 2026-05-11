class HeuristicSystem:
    def __init__(self, player, world_manager):
        self.player = player
        self.world_manager = world_manager

    def evaluate(self, enemies, items, in_hazard=False):
        hp_ratio = self.player.health / max(1.0, self.player.max_health)
        o2_ratio = self.player.oxygen / max(1.0, self.player.max_oxygen)
        food_ratio = self.player.hunger / max(1.0, self.player.max_hunger)

        if in_hazard:
            return "FLEE"

        if hp_ratio < 0.3:
            return "FLEE"

        if o2_ratio < 0.3:
            return "FIND_OXYGEN"
        if food_ratio < 0.3:
            return "FIND_FOOD"

        nearby_enemies = [
            e for e in enemies
            if ((e.x - self.player.x) ** 2 + (e.y - self.player.y) ** 2) ** 0.5 < 300
        ]
        if nearby_enemies:
            return "ATTACK"

        if items:
            return "LOOT"

        return "EXPLORE"
