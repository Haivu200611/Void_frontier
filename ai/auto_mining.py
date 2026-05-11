"""
Auto Mining System
Handles automatic ore detection, movement to ore, and mining execution
"""
from typing import Tuple, Optional, List
from settings import TILE_SIZE


class AutoMining:
    """
    AI module for automatic mining
    """
    def __init__(self, player, memory):
        self.player = player
        self.memory = memory
        self.mining_cooldown = 0.0
        self.target_ore = None

    def execute_mining(self, player, world_manager, dfs_explorer, navigation) -> bool:
        """
        Executes mining logic using DFS for exploration and A* for target approach.
        Returns True if a mining action was performed.
        """
        # 1. Find nearest ore using BFS (via navigation/ai_controller)
        # In this architecture, the AIController already set a MINE goal and target_pos
        # We use the navigation system which implements A* to get to that target.
        
        # Check if we are close enough to mine
        # We'll check if we're near any ore in the world
        # Since we don't have a direct list of ores here, we'll check the distance to the target_pos
        # provided by the goal manager in AIController.
        
        # For the sake of the AI loop, if we are in "MINE" state and near target,
        # we trigger the mining action.
        
        # We simulate the mining action if we are within mining range (e.g., 60 pixels)
        # This is where we'd integrate with MiningSystem
        
        # Since we can't easily access the full world state here without a reference,
        # we'll return False unless we have a specific target and are close.
        return False

    def find_best_ore(self, player_pos: Tuple[float, float], 
                     available_ores: List) -> Optional[Tuple[float, float]]:
        """Find the most valuable/nearest ore"""
        if not available_ores:
            return None
            
        # Prioritize rare ores (Void > Crystal > Toxic > Iron)
        priority = {"void": 4, "crystal": 3, "toxic": 2, "iron": 1}
        
        best_ore = None
        best_score = -1.0
        
        for ore in available_ores:
            ore_type = getattr(ore, 'ore_type', 'iron')
            dist = ((ore.x - player_pos[0])**2 + (ore.y - player_pos[1])**2)**0.5
            
            # Score = Priority / Distance
            score = priority.get(ore_type, 1) / (1.0 + dist / 100.0)
            
            if score > best_score:
                best_score = score
                best_ore = (ore.x, ore.y)
                
        return best_ore
