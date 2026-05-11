"""
Goal System for AI
Defines achievable objectives and their priority
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Callable, Dict, Any


class GoalType(Enum):
    """Types of AI goals"""
    EXPLORE = "explore"
    MINE = "mine"
    COMBAT = "combat"
    HEAL = "heal"
    ESCAPE = "escape"
    LOOT = "loot"
    TRADE = "trade"
    PORTAL = "portal"
    SURVIVE = "survive"


@dataclass
class Goal:
    """Base goal class"""
    goal_type: GoalType
    priority: float = 0.5  # 0.0 (low) to 1.0 (high)
    target: Optional[Any] = None
    target_pos: Optional[tuple] = None
    is_active: bool = True
    duration: float = 0.0  # How long we've been pursuing this goal
    max_duration: float = 60.0  # Max time before goal timeout
    completion_distance: float = 50.0  # Distance to target for completion
    
    def update(self, dt: float) -> None:
        """Update goal duration"""
        self.duration += dt
    
    def is_expired(self) -> bool:
        """Check if goal has exceeded max duration"""
        return self.duration > self.max_duration
    
    def is_completed(self, player_pos: tuple) -> bool:
        """Check if goal is completed"""
        if not self.target_pos:
            return False
        dx = self.target_pos[0] - player_pos[0]
        dy = self.target_pos[1] - player_pos[1]
        dist = (dx * dx + dy * dy) ** 0.5
        return dist <= self.completion_distance
    
    def get_priority_score(self) -> float:
        """Get adjusted priority score"""
        score = self.priority
        # Decrease priority over time
        time_penalty = (self.duration / self.max_duration) * 0.2
        return max(0.0, score - time_penalty)


@dataclass
class ExploreGoal(Goal):
    """Goal: Explore unknown areas"""
    goal_type: GoalType = GoalType.EXPLORE
    priority: float = 0.6
    max_duration: float = 120.0
    completion_distance: float = 100.0


@dataclass
class MineGoal(Goal):
    """Goal: Mine ore"""
    goal_type: GoalType = GoalType.MINE
    priority: float = 0.7
    max_duration: float = 30.0
    completion_distance: float = 120.0
    ore_type: Optional[str] = None
    min_ore_count: int = 3


@dataclass
class CombatGoal(Goal):
    """Goal: Fight enemy"""
    goal_type: GoalType = GoalType.COMBAT
    priority: float = 0.8
    max_duration: float = 20.0
    completion_distance: float = 0.0  # Kill target
    aggression_level: float = 1.0  # 0.0 (defensive) to 1.0 (aggressive)


@dataclass
class HealGoal(Goal):
    """Goal: Recover HP/resources"""
    goal_type: GoalType = GoalType.HEAL
    priority: float = 0.9  # High priority!
    max_duration: float = 20.0
    completion_distance: float = 50.0
    heal_amount_needed: float = 30.0


@dataclass
class EscapeGoal(Goal):
    """Goal: Flee from danger"""
    goal_type: GoalType = GoalType.ESCAPE
    priority: float = 1.0  # Highest priority!
    max_duration: float = 15.0
    completion_distance: float = 200.0
    escape_direction: tuple = field(default_factory=tuple)


@dataclass
class LootGoal(Goal):
    """Goal: Pick up items"""
    goal_type: GoalType = GoalType.LOOT
    priority: float = 0.5
    max_duration: float = 30.0
    completion_distance: float = 80.0


@dataclass
class TradeGoal(Goal):
    """Goal: Trade with NPC"""
    goal_type: GoalType = GoalType.TRADE
    priority: float = 0.65
    max_duration: float = 40.0
    completion_distance: float = 100.0


@dataclass
class PortalGoal(Goal):
    """Goal: Activate portal to next world"""
    goal_type: GoalType = GoalType.PORTAL
    priority: float = 0.6
    max_duration: float = 60.0
    completion_distance: float = 100.0


@dataclass
class SurviveGoal(Goal):
    """Goal: Basic survival (oxygen, hunger)"""
    goal_type: GoalType = GoalType.SURVIVE
    priority: float = 0.95
    max_duration: float = 120.0
    survival_type: str = "oxygen"  # or "hunger", "health"


class GoalManager:
    """
    Manages AI goals and priorities
    
    Responsible for:
    - Creating goals based on situation
    - Updating goal states
    - Selecting active goal
    - Handling goal completion/timeout
    """
    
    def __init__(self, player, blackboard, max_goals: int = 10):
        self.player = player
        self.blackboard = blackboard
        self.max_goals = max_goals
        
        self.active_goals: List[Goal] = []
        self.current_goal: Optional[Goal] = None
        self.completed_goals: List[Goal] = []
        self.failed_goals: List[Goal] = []
        
        self.goal_history: Dict[GoalType, int] = {}  # Track goal frequencies
    
    def create_goal(self, goal_type: GoalType, **kwargs) -> Goal:
        """Factory method to create goals"""
        goal_classes = {
            GoalType.EXPLORE: ExploreGoal,
            GoalType.MINE: MineGoal,
            GoalType.COMBAT: CombatGoal,
            GoalType.HEAL: HealGoal,
            GoalType.ESCAPE: EscapeGoal,
            GoalType.LOOT: LootGoal,
            GoalType.TRADE: TradeGoal,
            GoalType.PORTAL: PortalGoal,
            GoalType.SURVIVE: SurviveGoal,
        }
        
        goal_class = goal_classes.get(goal_type, Goal)
        return goal_class(**kwargs)
    
    def add_goal(self, goal: Goal) -> None:
        """Add goal to active list, avoiding duplicates of same type and target"""
        # Check for existing goal of same type
        for existing in self.active_goals:
            if existing.goal_type == goal.goal_type:
                if existing.target == goal.target or (not existing.target and not goal.target):
                    # Update priority/duration instead of adding duplicate
                    existing.priority = max(existing.priority, goal.priority)
                    existing.target_pos = goal.target_pos
                    existing.duration = 0 # Reset duration
                    return
                    
        if len(self.active_goals) < self.max_goals:
            self.active_goals.append(goal)
        else:
            # Replace lowest priority goal if new one is higher
            self.active_goals.sort(key=lambda g: g.get_priority_score())
            if goal.priority > self.active_goals[0].get_priority_score():
                self.active_goals[0] = goal
    
    def remove_goal(self, goal: Goal) -> None:
        """Remove goal from active list"""
        if goal in self.active_goals:
            self.active_goals.remove(goal)
    
    def select_best_goal(self) -> Optional[Goal]:
        """Select best goal based on priority and context"""
        if not self.active_goals:
            return None
        
        # Filter out expired goals
        valid_goals = [g for g in self.active_goals if not g.is_expired()]
        
        if not valid_goals:
            self.active_goals.clear()
            return None
        
        # Sort by priority
        valid_goals.sort(key=lambda g: g.get_priority_score(), reverse=True)
        return valid_goals[0]
    
    def update(self, dt: float) -> None:
        """Update all goals"""
        # Update goal durations
        for goal in self.active_goals:
            goal.update(dt)
        
        # Check for completion/expiration
        completed = []
        expired = []
        
        for goal in self.active_goals:
            if goal.is_completed((self.player.x, self.player.y)):
                completed.append(goal)
            elif goal.is_expired():
                expired.append(goal)
        
        # Move completed goals
        for goal in completed:
            self.active_goals.remove(goal)
            self.completed_goals.append(goal)
            self.goal_history[goal.goal_type] = self.goal_history.get(goal.goal_type, 0) + 1
        
        # Move expired goals
        for goal in expired:
            self.active_goals.remove(goal)
            self.failed_goals.append(goal)
        
        # Select best active goal
        self.current_goal = self.select_best_goal()
        
        if self.current_goal:
            self.blackboard.set_goal(self.current_goal.goal_type.value, 
                                    self.current_goal.target)
    
    def suggest_goals(self, environment_state: Dict[str, Any]) -> List[Goal]:
        """
        Suggest goals based on current environment state
        Engine for intelligent decision making
        """
        suggestions = []
        
        hp_ratio = environment_state.get("hp_ratio", 1.0)
        oxygen_ratio = environment_state.get("oxygen_ratio", 1.0)
        hunger_ratio = environment_state.get("hunger_ratio", 1.0)
        inventory_full = environment_state.get("inventory_full", False)
        nearby_enemies = environment_state.get("nearby_enemies", [])
        nearby_ores = environment_state.get("nearby_ores", [])
        nearby_items = environment_state.get("nearby_items", [])
        nearby_npcs = environment_state.get("nearby_npcs", [])
        threat_level = environment_state.get("threat_level", 0.0)
        current_biome = environment_state.get("current_biome", "unknown")
        player_pos = (self.player.x, self.player.y)
        
        # ESCAPE if critical threat
        if threat_level > 0.8 or (nearby_enemies and threat_level > 0.5):
            escape_goal = self.create_goal(
                GoalType.ESCAPE,
                priority=1.0,
                target=nearby_enemies[0] if nearby_enemies else None
            )
            suggestions.append(escape_goal)
        
        # HEAL if HP critical
        if hp_ratio < 0.3:
            heal_goal = self.create_goal(
                GoalType.HEAL,
                priority=0.95,
                heal_amount_needed=self.player.max_health * 0.5
            )
            suggestions.append(heal_goal)
        
        # SURVIVE: Oxygen critical
        if oxygen_ratio < 0.2:
            survive_goal = self.create_goal(
                GoalType.SURVIVE,
                priority=0.95,
                survival_type="oxygen"
            )
            suggestions.append(survive_goal)
        
        # SURVIVE: Hunger critical
        if hunger_ratio < 0.2:
            survive_goal = self.create_goal(
                GoalType.SURVIVE,
                priority=0.92,
                survival_type="hunger"
            )
            suggestions.append(survive_goal)
        
        # COMBAT if enemy nearby or known in memory
        if hp_ratio > 0.5 and threat_level < 0.8:
            auto_combat_entities = environment_state.get("auto_combat_entities", True)
            auto_combat_boss = environment_state.get("auto_combat_boss", True)
            
            target_enemy = None
            if nearby_enemies:
                for enemy in nearby_enemies:
                    is_boss = hasattr(enemy, "phase") or "Boss" in str(type(enemy))
                    if is_boss and not auto_combat_boss: continue
                    if not is_boss and not auto_combat_entities: continue
                    target_enemy = enemy
                    break
            else:
                # Search memory for enemy spawns if no enemies nearby
                enemy_spawns = [loc for loc in self.blackboard.known_locations.values() 
                               if loc.location_type == "enemy_spawn"]
                if enemy_spawns:
                    # Sort by distance
                    enemy_spawns.sort(key=lambda l: ((l.x - player_pos[0])**2 + (l.y - player_pos[1])**2))
                    target_enemy = enemy_spawns[0]

            if target_enemy:
                combat_goal = self.create_goal(
                    GoalType.COMBAT,
                    priority=0.8,
                    target=target_enemy,
                    target_pos=(target_enemy.x, target_enemy.y),
                    aggression_level=min(1.0, (1.0 - threat_level))
                )
                suggestions.append(combat_goal)
        
        # MINE if ores nearby or known in memory, and inventory not full
        if not inventory_full and environment_state.get("auto_mine", True):
            target_ore = None
            if nearby_ores:
                target_ore = nearby_ores[0]
            else:
                # Check memory for known ores if none nearby
                known_ores = self.blackboard.get_nearest_ores(max_count=1)
                if known_ores:
                    target_ore = known_ores[0]
            
            if target_ore:
                # Use 'resources' for memory objects, 'subtype' for observations
                ore_type_val = getattr(target_ore, 'subtype', None)
                if ore_type_val is None:
                    ore_type_val = getattr(target_ore, 'resources', 'Iron Ore')
                
                mine_goal = self.create_goal(
                    GoalType.MINE,
                    priority=0.7,
                    target=target_ore,
                    target_pos=(target_ore.x, target_ore.y),
                    ore_type=ore_type_val
                )
                suggestions.append(mine_goal)
        
        # LOOT if items nearby and inventory has space
        if nearby_items and not inventory_full:
            # High priority if very close, otherwise moderate
            item_dist = nearby_items[0].distance
            loot_prio = 0.85 if item_dist < 150 else 0.65
            
            loot_goal = self.create_goal(
                GoalType.LOOT,
                priority=loot_prio,
                target=nearby_items[0],
                target_pos=(nearby_items[0].x, nearby_items[0].y)
            )
            suggestions.append(loot_goal)
        
        # TRADE if inventory full and NPC nearby
        if inventory_full and nearby_npcs:
            trade_goal = self.create_goal(
                GoalType.TRADE,
                priority=0.75,
                target=nearby_npcs[0],
                target_pos=(nearby_npcs[0].x, nearby_npcs[0].y)
            )
            suggestions.append(trade_goal)
        
        # EXPLORE (always an option)
        explore_goal = self.create_goal(GoalType.EXPLORE, priority=0.6)
        suggestions.append(explore_goal)
        
        return suggestions
    
    def get_debug_info(self) -> Dict[str, Any]:
        """Get debug information"""
        return {
            "active_goals": len(self.active_goals),
            "current_goal": self.current_goal.goal_type.value if self.current_goal else None,
            "current_goal_priority": self.current_goal.priority if self.current_goal else 0.0,
            "completed_goals": len(self.completed_goals),
            "failed_goals": len(self.failed_goals),
            "goal_history": self.goal_history,
        }
