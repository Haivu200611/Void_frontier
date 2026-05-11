"""
Trading System
Handles logic for trading with NPCs
"""

class TradingSystem:
    def __init__(self, inventory, progression_manager):
        self.inventory = inventory
        self.progression_manager = progression_manager
        
    def can_trade_for_repair_kit(self):
        """Check if we have all 3 artifacts"""
        return self.progression_manager.check_endgame_ready()

    def perform_trade_for_repair_kit(self):
        if self.can_trade_for_repair_kit() and not self.progression_manager.has_ship_repair_kit:
            self.progression_manager.has_ship_repair_kit = True
            self.inventory.add_item("quest_ship_repair_kit", 1)
            # Remove artifacts from inventory
            self.inventory.remove_item("quest_artifact_alpha", 1)
            self.inventory.remove_item("quest_artifact_beta", 1)
            self.inventory.remove_item("quest_artifact_gamma", 1)
            return True
        return False

    def trade_for_upgrade_pickaxe(self):
        """Trade 15 Meteor Ore for Upgraded Pickaxe"""
        if self.inventory.has_item("item_meteor_ore", 15):
            self.inventory.remove_item("item_meteor_ore", 15)
            self.inventory.add_item("tool_crystal_pickaxe", 1)
            return True
        return False

    def trade_for_upgrade_gun(self):
        """Trade 15 Meteor Ore for Upgraded Gun"""
        if self.inventory.has_item("item_meteor_ore", 15):
            self.inventory.remove_item("item_meteor_ore", 15)
            self.inventory.add_item("weapon_plasma_gun", 1)
            return True
        return False
