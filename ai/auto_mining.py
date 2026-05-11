"""
Auto Mining System
Handles automatic ore detection, movement to ore, and mining execution
"""
from typing import Tuple, Optional, List
from entities.ore import OreType
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

    def execute_mining(self, player, world_manager, mining_system, goal) -> bool:
        """
        Executes mining logic.
        Checks if player is near the goal's target ore and triggers mining damage.
        """
        if not goal or not goal.target:
            return False
            
        target_ore = goal.target
        
        # Check if ore is already dead
        if getattr(target_ore, 'is_dead', False):
            return False
            
        # Calculate distance to target ore
        dist = ((target_ore.x - player.x)**2 + (target_ore.y - player.y)**2)**0.5
        
        # Mining range (slightly less than MiningSystem's range for stability)
        if dist <= 110.0:
            # Check cooldown in MiningSystem
            if mining_system.cooldown_timer <= 0:
                # Simulate mining hit
                # We need to resolve tool stats manually or use try_mine logic
                # For simplicity, we'll use base damage if we can't easily access tool stats
                
                tool_stack = player.inventory.get_active_tool_stack() if hasattr(player, "inventory") else None
                stats = mining_system._resolve_tool_stats(tool_stack.item_id if tool_stack else None)
                
                damage = mining_system.base_damage * stats.mining_speed * stats.efficiency
                mined = target_ore.take_mining_damage(damage, stats.mining_power)
                mining_system.cooldown_timer = max(0.08, stats.cooldown)
                
                if mined:
                    mining_system._consume_tool_durability(player, tool_stack)
                    # Feedback for AI
                    if target_ore.is_dead:
                        mining_system._set_feedback(f"Mined {target_ore.ore_type}")
                    else:
                        mining_system._set_feedback(f"Mining {target_ore.ore_type}...")
                    return True
                    
        return False

    def find_best_ore(self, player_pos: Tuple[float, float], 
                     available_ores: List) -> Optional[Tuple[float, float]]:
        """Find the most valuable/nearest ore"""
        if not available_ores:
            return None
            
        # Prioritize rare ores (Void > Crystal > Toxic > Iron)
        priority = {
            OreType.VOID: 5,
            OreType.METEOR: 4,
            OreType.CRYSTAL: 3,
            OreType.TOXIC: 2,
            OreType.IRON: 1
        }
        
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
