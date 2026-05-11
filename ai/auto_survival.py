from systems.items import ItemDatabase


class AutoSurvival:
    """
    AI module for survival management
    - Auto-use oxygen packs
    - Auto-use food
    - Auto-use medkits
    """
    def __init__(self, player):
        self.player = player
        self.use_cooldown = 0.0
        self.cooldown_time = 1.0  # 1 second between consumable uses
        
    def manage_survival(self, player, inventory) -> None:
        """
        Check survival stats and use items from inventory if needed
        """
        if inventory is None:
            return
            
        if self.use_cooldown > 0:
            self.use_cooldown -= 0.016 # Approx dt
            return
            
        # Priority 1: Health (Critical)
        if player.health < player.max_health * 0.3:
            if self._use_item_by_type(inventory, "heal"):
                self.use_cooldown = self.cooldown_time
                return
                
        # Priority 2: Oxygen (Critical)
        if player.oxygen < player.max_oxygen * 0.2:
            if self._use_item_by_type(inventory, "oxygen"):
                self.use_cooldown = self.cooldown_time
                return
                
        # Priority 3: Hunger (Low)
        if player.hunger < player.max_hunger * 0.2:
            if self._use_item_by_type(inventory, "hunger"):
                self.use_cooldown = self.cooldown_time
                return

    def _use_item_by_type(self, inventory, effect_key: str) -> bool:
        """
        Find and use an item with a specific effect in inventory
        """
        # Search inventory for item with effect
        for i, slot in enumerate(inventory.slots):
            if slot:
                item_data = ItemDatabase.get_item(slot.item_id)
                if item_data and item_data.type == "consumable":
                    effects = item_data.consumable_effects
                    if effect_key in effects:
                        # Use the item
                        val = effects[effect_key]
                        if effect_key == "heal":
                            self.player.health = min(self.player.max_health, self.player.health + val)
                        elif effect_key == "oxygen":
                            self.player.oxygen = min(self.player.max_oxygen, self.player.oxygen + val)
                        elif effect_key == "hunger":
                            self.player.hunger = min(self.player.max_hunger, self.player.hunger + val)
                        
                        # Consume one item
                        slot.count -= 1
                        if slot.count <= 0:
                            inventory.slots[i] = None
                        
                        return True
        return False
