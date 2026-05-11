"""
AI Controller
Central orchestrator for all AI systems
Integrates: Blackboard, Memory, Pathfinding, Goals, Danger Map, etc.
"""
from typing import Optional, Dict, List, Any, Tuple
from ai.blackboard import AIBlackboard
from ai.memory import AIMemory
from ai.navigation import NavigationController
from ai.bfs import BFSScanner
from ai.dfs import DFSExplorer
from ai.goals import GoalManager, GoalType
from ai.danger_map import DangerMap
from ai.combat_ai import CombatAI
from ai.auto_mining import AutoMining
from ai.auto_survival import AutoSurvival
from settings import TILE_SIZE


class AIController:
    """
    Main AI brain for player or entity
    
    Update loop:
    1. Sense: Update blackboard with environment
    2. Think: Update memory & danger map
    3. Decide: Generate & select goals
    4. Plan: Build path to goal
    5. Execute: Move & act
    6. Reevaluate: Check if goal still valid
    """
    
    def __init__(self, player, world_manager, pathfinding, mining_system=None):
        self.player = player
        self.world_manager = world_manager
        self.pathfinding = pathfinding
        self.mining_system = mining_system
        
        # Core AI systems
        self.blackboard = AIBlackboard(player, world_manager, scan_radius=800.0)
        self.memory = AIMemory(tile_size=TILE_SIZE)
        self.danger_map = DangerMap()
        self.goal_manager = GoalManager(player, self.blackboard)
        
        # Navigation
        self.navigation = NavigationController(pathfinding, world_manager, TILE_SIZE)
        
        # Resource scanners
        self.bfs_scanner = BFSScanner(world_manager, TILE_SIZE)
        self.dfs_explorer = DFSExplorer(world_manager, self.memory, TILE_SIZE)
        
        # Behavior state
        self.current_action: Optional[str] = None
        self.attack_target: Optional[Any] = None
        self.last_decision_time: float = 0.0
        self.decision_interval: float = 0.5  # Decide every 0.5s
        
        # Stats
        self.frames_processed: int = 0
        self.goals_completed: int = 0
        self.goals_failed: int = 0
        
        # Performance throttling
        self.sensor_throttle: int = 0
        self.sensor_update_rate: int = 2  # Update every 2 frames
        
        # Combat, mining and survival modules
        self.combat_ai = CombatAI(self.player, self.blackboard, self.danger_map)
        self.mining_ai = AutoMining(self.player, self.memory)
        self.survival_ai = AutoSurvival(self.player)
        
        # Hold last seen full enemy objects (populated each update)
        self._last_seen_enemies: List = []
    
    def update(self, dt: float, 
              enemies: List, items: List, ores: List, npcs: List, portals: List,
              projectile_pool=None,
              current_hazard_zone: Optional[Tuple] = None,
              current_biome: str = "unknown",
              auto_mine=False, auto_combat_entities=False, auto_combat_boss=False) -> None:
        """
        Main update loop
        Executes: Sense → Think → Decide → Plan → Execute → Reevaluate
        """
        self.auto_mine = auto_mine
        self.auto_combat_entities = auto_combat_entities
        self.auto_combat_boss = auto_combat_boss
        # === SENSE ===
        if self.sensor_throttle % self.sensor_update_rate == 0:
            self.blackboard.update_environment(
                enemies, items, ores, npcs, portals,
                current_hazard_zone, current_biome
            )
        self.sensor_throttle += 1
        
        # === THINK ===
        self._update_memory(current_biome)
        self._update_danger_map(enemies, items)
        # store full enemy list for combat AI
        self._last_seen_enemies = enemies
        
        # === DECIDE ===
        self.last_decision_time += dt
        if self.last_decision_time >= self.decision_interval:
            self._select_goal()
            self.last_decision_time = 0.0
        
        # === PLAN ===
        self._plan_action(dt)
        
        # === EXECUTE ===
        self._execute_action(dt, projectile_pool)
        
        # === REEVALUATE ===
        self._reevaluate_goal()
        
        self.frames_processed += 1
    
    def _update_memory(self, current_biome: str) -> None:
        """Update AI memory with exploration data"""
        player_chunk_x = int(self.player.x / (32 * TILE_SIZE))
        player_chunk_y = int(self.player.y / (32 * TILE_SIZE))
        
        # Mark current chunk as visited
        self.memory.mark_chunk_visited(player_chunk_x, player_chunk_y)
        
        # Mark current tile as explored
        self.memory.mark_tile_explored(self.player.x, self.player.y)
        
        # Check for stuck situations
        if self.memory.track_stuck(self.player.x, self.player.y):
            # AI is stuck, might need to backtrack
            pass
    
    def _update_danger_map(self, enemies: List, items: List) -> None:
        """Update danger map from environment"""
        self.danger_map.update(0.016)  # Approximate dt
        
        # Add enemy threats
        for obs in self.blackboard.environment.nearby_enemies:
            # Reconstruct enemy object reference from observation
            # For now, just use the observation data
            self.danger_map.add_enemy_threat(
                obs.x, obs.y,
                obs.health if obs.health else 60,
                100.0,  # Assuming max health of 100
                radius=300.0
            )
        
        # Add hazard
        if self.blackboard.environment.in_hazard:
            hazard_type = self.blackboard.environment.hazard_type
            self.danger_map.add_hazard_zone(
                self.player.x, self.player.y,
                hazard_type or "unknown",
                radius=150.0,
                severity=0.8
            )
        
        # Add crowd threat if multiple enemies
        if len(self.blackboard.environment.nearby_enemies) > 2:
            self.danger_map.add_crowd_threat([], radius=250.0)
    
    def _select_goal(self) -> None:
        """Generate and select best goal using Heuristic evaluation"""
        # Build environment state for goal manager
        env_state = {
            "hp_ratio": self.player.health / max(1.0, self.player.max_health),
            "oxygen_ratio": self.player.oxygen / max(1.0, self.player.max_oxygen),
            "hunger_ratio": self.player.hunger / max(1.0, self.player.max_hunger),
            "inventory_full": self.blackboard.environment.player_inventory_full,
            "nearby_enemies": self.blackboard.environment.nearby_enemies,
            "nearby_ores": self.blackboard.environment.nearby_ores,
            "nearby_items": self.blackboard.environment.nearby_items,
            "nearby_npcs": self.blackboard.environment.nearby_npcs,
            "threat_level": self.danger_map.global_danger_level,
            "current_biome": self.blackboard.environment.current_biome,
            "auto_mine": getattr(self, 'auto_mine', False),
            "auto_combat_entities": getattr(self, 'auto_combat_entities', False),
            "auto_combat_boss": getattr(self, 'auto_combat_boss', False),
        }
        
        # Get suggested goals using Heuristic-based GoalManager
        suggestions = self.goal_manager.suggest_goals(env_state)
        
        # Add to active goals
        for goal in suggestions:
            self.goal_manager.add_goal(goal)
        
        # Update goal manager
        self.goal_manager.update(0.016) # Use consistent dt
        
        # Get current goal
        current_goal = self.goal_manager.current_goal
        if current_goal:
            self.current_action = current_goal.goal_type.value
            if current_goal.target:
                self.attack_target = current_goal.target
    
    def _plan_action(self, dt: float) -> None:
        """Plan path/action for current goal"""
        goal = self.goal_manager.current_goal
        if not goal:
            self.player.velocity_x = 0
            self.player.velocity_y = 0
            return
        
        # Different planning for different goal types
        if goal.goal_type == GoalType.EXPLORE:
            self._plan_explore(dt)
        elif goal.goal_type == GoalType.MINE:
            self._plan_mine(goal, dt)
        elif goal.goal_type == GoalType.COMBAT:
            self._plan_combat(goal, dt)
        elif goal.goal_type == GoalType.HEAL:
            self._plan_heal(goal, dt)
        elif goal.goal_type == GoalType.ESCAPE:
            self._plan_escape(goal, dt)
        elif goal.goal_type == GoalType.LOOT:
            self._plan_loot(goal, dt)
        elif goal.goal_type == GoalType.TRADE:
            self._plan_trade(goal, dt)
        elif goal.goal_type == GoalType.SURVIVE:
            self._plan_survive(goal, dt)
        else:
            self.player.velocity_x = 0
            self.player.velocity_y = 0
    
    def _plan_explore(self, dt: float) -> None:
        """Plan exploration path using DFS"""
        # Use DFS to find next exploration frontier
        next_target = self.dfs_explorer.get_next_exploration_target(
            (self.player.x, self.player.y),
            self.memory.explored_tiles,
            self.memory
        )
        
        if not next_target:
            # Random exploration if no target found
            import random
            import math
            for _ in range(10): # Try 10 times to find walkable random target
                angle = random.random() * 2 * math.pi
                distance = 300 + random.random() * 200
                tx = (self.player.x + math.cos(angle) * distance)
                ty = (self.player.y + math.sin(angle) * distance)
                
                # Check if walkable
                itx, ity = int(tx // TILE_SIZE), int(ty // TILE_SIZE)
                if self.pathfinding.is_walkable(itx, ity):
                    next_target = (tx, ty)
                    break
            
            if not next_target:
                # Fallback to current pos if nothing found (rare)
                next_target = (self.player.x, self.player.y)
        
        # Plan path using A* (via navigation.update_path)
        self.navigation.update_path(
            (self.player.x, self.player.y),
            next_target,
            avoid_hazards=True,
            avoid_enemies=False,
            dt=dt
        )
    
    def _plan_mine(self, goal, dt: float) -> None:
        """Plan mining approach"""
        if goal.target_pos:
            self.navigation.update_path(
                (self.player.x, self.player.y),
                goal.target_pos,
                avoid_hazards=True,
                avoid_enemies=True,
                dt=dt
            )
    
    def _plan_combat(self, goal, dt: float) -> None:
        """Plan combat engagement using A* for positioning"""
        # Combat planning handled by CombatAI during execution.
        # We use A* (via navigation) to maintain a path toward the target for fallback.
        if goal.target_pos:
            self.navigation.update_path(
                (self.player.x, self.player.y),
                goal.target_pos,
                avoid_hazards=True,
                avoid_enemies=False,
                dt=dt
            )
    
    def _plan_heal(self, goal, dt: float) -> None:
        """Plan to reach safe zone or healing item"""
        # Find safe zone
        safe_zones = self.danger_map.get_safe_zones(
            self.player.x, self.player.y,
            safe_threshold=0.3
        )
        
        if safe_zones:
            self.navigation.update_path(
                (self.player.x, self.player.y),
                safe_zones[0],
                avoid_hazards=True,
                avoid_enemies=True,
                dt=dt
            )
    
    def _plan_escape(self, goal, dt: float) -> None:
        """Plan escape from danger"""
        # Get escape direction
        escape_dx, escape_dy = self.danger_map.get_escape_direction(
            self.player.x, self.player.y
        )
        
        # Move in escape direction
        escape_distance = 400
        escape_target = (
            self.player.x + escape_dx * escape_distance,
            self.player.y + escape_dy * escape_distance
        )
        
        self.navigation.update_path(
            (self.player.x, self.player.y),
            escape_target,
            avoid_hazards=True,
            avoid_enemies=True,
            dt=dt
        )
    
    def _plan_loot(self, goal, dt: float) -> None:
        """Plan to reach loot"""
        if goal.target_pos:
            self.navigation.update_path(
                (self.player.x, self.player.y),
                goal.target_pos,
                avoid_hazards=False,
                avoid_enemies=False,
                dt=dt
            )
    
    def _plan_trade(self, goal, dt: float) -> None:
        """Plan to reach trader"""
        if goal.target_pos:
            self.navigation.update_path(
                (self.player.x, self.player.y),
                goal.target_pos,
                avoid_hazards=True,
                avoid_enemies=True,
                dt=dt
            )
    
    def _plan_survive(self, goal, dt: float) -> None:
        """Plan for survival needs"""
        # Find safe zone or resource based on need
        if goal.survival_type == "oxygen":
            # Go to safe zone for oxygen recovery
            safe_zones = self.danger_map.get_safe_zones(
                self.player.x, self.player.y
            )
            if safe_zones:
                self.navigation.update_path(
                    (self.player.x, self.player.y),
                    safe_zones[0],
                    avoid_hazards=True,
                    avoid_enemies=True,
                    dt=dt
                )
    
    def _execute_action(self, dt: float, projectile_pool=None) -> None:
        """Execute planned movement and actions"""
        # Priority 1: Survival (use consumables)
        self.survival_ai.manage_survival(self.player, getattr(self.player, 'inventory', None))

        # Priority 2: Combat — if current goal is combat or there's immediate threat
        goal = self.goal_manager.current_goal
        in_combat_mode = goal and goal.goal_type == GoalType.COMBAT
        immediate_threat = self.danger_map.global_danger_level > 0.2 and len(self._last_seen_enemies) > 0

        if in_combat_mode or immediate_threat:
            vx, vy = self.combat_ai.execute_combat(self._last_seen_enemies, projectile_pool)
            self.player.velocity_x = vx
            self.player.velocity_y = vy
            return

        # Priority 3: Mining
        if goal and goal.goal_type == GoalType.MINE and self.mining_ai and self.mining_system:
            did_mine = self.mining_ai.execute_mining(self.player, self.world_manager, self.mining_system, goal)
            if did_mine:
                # Mining action performed; stop movement this frame
                self.player.velocity_x = 0
                self.player.velocity_y = 0
                return

        # Fallback: Follow navigation path
        waypoint = self.navigation.get_next_waypoint()
        if waypoint:
            dx = waypoint[0] - self.player.x
            dy = waypoint[1] - self.player.y
            dist = (dx * dx + dy * dy) ** 0.5
            
            if dist < 15:
                # Reached waypoint
                self.navigation.advance_waypoint()
            else:
                # Move toward waypoint
                speed = self.player.base_speed * self.player.status_speed_multiplier
                self.player.velocity_x = (dx / dist) * speed
                self.player.velocity_y = (dy / dist) * speed
        else:
            # No waypoint - if we have a target_pos, try moving directly if close
            if goal and goal.target_pos:
                gdx = goal.target_pos[0] - self.player.x
                gdy = goal.target_pos[1] - self.player.y
                gdist = (gdx * gdx + gdy * gdy) ** 0.5
                if gdist > 20:
                    speed = self.player.base_speed * self.player.status_speed_multiplier
                    self.player.velocity_x = (gdx / gdist) * speed
                    self.player.velocity_y = (gdy / gdist) * speed
                else:
                    self.player.velocity_x = 0
                    self.player.velocity_y = 0
            else:
                self.player.velocity_x = 0
                self.player.velocity_y = 0
        
        # Handle combat (legacy/fallback)
        if self.attack_target:
            target = self.attack_target
            dist = ((target.x - self.player.x) ** 2 + (target.y - self.player.y) ** 2) ** 0.5
            
            if dist < 100:
                # In attack range
                if not self.player.is_attacking and self.player.attack_timer <= 0:
                    self.player.is_attacking = True
                    self.player.attack_timer = self.player.attack_cooldown
                    self.player.attack_box.activate()
                    # Point attack at target
                    if dist > 0:
                        self.player.attack_box.offset_x = (target.x - self.player.x) * 0.5
                        self.player.attack_box.offset_y = (target.y - self.player.y) * 0.5
    
    def _reevaluate_goal(self) -> None:
        """Periodically check if goal is still valid"""
        goal = self.goal_manager.current_goal
        if not goal:
            return
        
        # Goal is no longer valid if:
        # 1. Target disappeared
        # 2. Situation changed dramatically
        # 3. Time expired
        if goal.target and (not hasattr(goal.target, 'is_dead') or goal.target.is_dead):
            self.goal_manager.remove_goal(goal)
        
        # Check if situation changed
        if goal.goal_type == GoalType.COMBAT:
            threat = self.danger_map.global_danger_level
            hp_ratio = self.player.health / max(1.0, self.player.max_health)
            
            if threat > 0.8 and hp_ratio < 0.3:
                # Too much danger, escape instead
                self.goal_manager.remove_goal(goal)
    
    def get_debug_info(self) -> Dict[str, Any]:
        """Get debug information for rendering"""
        goal = self.goal_manager.current_goal
        return {
            "current_goal": goal.goal_type.value if goal else "None",
            "current_action": self.current_action or "Idle",
            "threat_level": self.danger_map.global_danger_level,
            "active_goals": len(self.goal_manager.active_goals),
            "path_length": len(self.navigation.current_path),
            "path_index": self.navigation.path_index,
            "explored_chunks": len(self.memory.visited_chunks),
            "frames_processed": self.frames_processed,
            "blackboard_info": self.blackboard.get_debug_info(),
            "danger_map_info": self.danger_map.get_debug_info(),
        }
