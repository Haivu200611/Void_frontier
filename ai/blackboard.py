"""
AI Blackboard System
Shared world knowledge & memory for AI decision-making
"""
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Set
from enum import Enum


class TargetType(Enum):
    """Types of targets the AI can pursue"""
    ENEMY = "enemy"
    ORE = "ore"
    LOOT = "loot"
    NPC = "npc"
    PORTAL = "portal"
    HEALING_ZONE = "healing_zone"
    OXYGEN_SOURCE = "oxygen_source"


@dataclass
class EntityObservation:
    """Snapshot of an observed entity"""
    entity_id: int
    entity_type: TargetType
    x: float
    y: float
    distance: float
    health: float = None  # For enemies
    threat_level: float = 0.0  # For danger assessment
    last_seen_time: float = 0.0  # When we last saw this


@dataclass
class LocationMemory:
    """Remembered location (ore, hazard, safe zone, etc.)"""
    x: float
    y: float
    location_type: str  # "ore_spawn", "hazard_zone", "safe_zone", "npc", "portal"
    discovered_time: float = 0.0
    last_visited_time: float = 0.0
    reliability: float = 1.0  # How confident are we about this location (0.0-1.0)
    resources: Optional[str] = None  # For ore type, hazard type, etc.


@dataclass
class EnvironmentSnapshot:
    """Current environmental state snapshot"""
    player_x: float
    player_y: float
    player_health: float
    player_oxygen: float
    player_hunger: float
    player_inventory_full: bool = False
    in_hazard: bool = False
    hazard_type: Optional[str] = None
    current_biome: str = "unknown"
    nearby_enemies: List[EntityObservation] = field(default_factory=list)
    nearby_ores: List[EntityObservation] = field(default_factory=list)
    nearby_items: List[EntityObservation] = field(default_factory=list)
    nearby_npcs: List[EntityObservation] = field(default_factory=list)
    nearby_portals: List[EntityObservation] = field(default_factory=list)


class AIBlackboard:
    """
    Central knowledge repository for AI system
    
    Serves as:
    - Sensor data cache (what AI perceives)
    - Memory system (what AI remembers)
    - Goal tracker (what AI wants to do)
    - Shared state (accessible by all AI modules)
    """
    
    def __init__(self, player, world_manager, scan_radius: float = 800.0):
        self.player = player
        self.world_manager = world_manager
        self.scan_radius = scan_radius
        
        # Current snapshot (updated each frame)
        self.environment: EnvironmentSnapshot = EnvironmentSnapshot(
            player_x=player.x,
            player_y=player.y,
            player_health=player.health,
            player_oxygen=player.oxygen,
            player_hunger=player.hunger,
        )
        
        # Long-term memory
        self.known_locations: Dict[Tuple[int, int], LocationMemory] = {}
        self.explored_chunks: Set[Tuple[int, int]] = set()
        self.discovered_ore_types: Dict[str, List[LocationMemory]] = {
            "iron": [], "crystal": [], "toxic": [], "void": []
        }
        self.hazard_zones: List[LocationMemory] = []
        self.safe_zones: List[LocationMemory] = []
        self.npc_locations: List[LocationMemory] = []
        self.portal_locations: List[LocationMemory] = []
        
        # Goal & behavior tracking
        self.current_goal: Optional[str] = None
        self.goal_target: Optional[EntityObservation] = None
        self.goal_changed_frame: int = 0
        
        # Temporal data
        self.last_update_time: float = 0.0
        self.last_threat_assessment: float = 0.0
        self.threat_level: float = 0.0  # 0.0 (safe) to 1.0 (critical)
        
        # Performance tracking
        self.memory_access_count: int = 0
        self.decision_cache: Dict[str, any] = {}
        
    # ========== SENSOR UPDATES ==========
    
    def update_environment(self, 
                          enemies: List, 
                          items: List,
                          ores: List, 
                          npcs: List,
                          portals: List,
                          current_hazard_zone: Optional[Tuple[str, Tuple[float, float], float]] = None,
                          current_biome: str = "unknown") -> None:
        """
        Update blackboard with current sensory data
        Called once per frame from main AI update loop
        """
        self.environment.player_x = self.player.x
        self.environment.player_y = self.player.y
        self.environment.player_health = self.player.health
        self.environment.player_oxygen = self.player.oxygen
        self.environment.player_hunger = self.player.hunger
        self.environment.player_inventory_full = self.player.inventory.is_full()
        self.environment.current_biome = current_biome
        
        # Hazard info
        if current_hazard_zone:
            self.environment.in_hazard = True
            self.environment.hazard_type = current_hazard_zone[0]
        else:
            self.environment.in_hazard = False
            self.environment.hazard_type = None
        
        # Clear previous observations
        self.environment.nearby_enemies.clear()
        self.environment.nearby_ores.clear()
        self.environment.nearby_items.clear()
        self.environment.nearby_npcs.clear()
        self.environment.nearby_portals.clear()
        
        # Scan entities within radius
        player_pos = (self.player.x, self.player.y)
        
        # Enemies
        for enemy in enemies:
            if self._in_range(player_pos, (enemy.x, enemy.y)):
                obs = EntityObservation(
                    entity_id=id(enemy),
                    entity_type=TargetType.ENEMY,
                    x=enemy.x,
                    y=enemy.y,
                    distance=self._distance(player_pos, (enemy.x, enemy.y)),
                    health=enemy.health,
                    threat_level=self._calculate_threat(enemy),
                    last_seen_time=self.last_update_time,
                )
                self.environment.nearby_enemies.append(obs)
        
        # Ores
        for ore in ores:
            if self._in_range(player_pos, (ore.x, ore.y)):
                obs = EntityObservation(
                    entity_id=id(ore),
                    entity_type=TargetType.ORE,
                    x=ore.x,
                    y=ore.y,
                    distance=self._distance(player_pos, (ore.x, ore.y)),
                    health=ore.health,
                    last_seen_time=self.last_update_time,
                )
                self.environment.nearby_ores.append(obs)
                # Remember ore location
                self._remember_location(ore.x, ore.y, "ore_spawn", 
                                      resources=getattr(ore, 'ore_type', 'iron'))
        
        # Items
        for item in items:
            if self._in_range(player_pos, (item.x, item.y)):
                obs = EntityObservation(
                    entity_id=id(item),
                    entity_type=TargetType.LOOT,
                    x=item.x,
                    y=item.y,
                    distance=self._distance(player_pos, (item.x, item.y)),
                    last_seen_time=self.last_update_time,
                )
                self.environment.nearby_items.append(obs)
        
        # NPCs
        for npc in npcs:
            if self._in_range(player_pos, (npc.x, npc.y)):
                obs = EntityObservation(
                    entity_id=id(npc),
                    entity_type=TargetType.NPC,
                    x=npc.x,
                    y=npc.y,
                    distance=self._distance(player_pos, (npc.x, npc.y)),
                    last_seen_time=self.last_update_time,
                )
                self.environment.nearby_npcs.append(obs)
                self._remember_location(npc.x, npc.y, "npc")
        
        # Portals
        for portal in portals:
            if self._in_range(player_pos, (portal.x, portal.y)):
                obs = EntityObservation(
                    entity_id=id(portal),
                    entity_type=TargetType.PORTAL,
                    x=portal.x,
                    y=portal.y,
                    distance=self._distance(player_pos, (portal.x, portal.y)),
                    last_seen_time=self.last_update_time,
                )
                self.environment.nearby_portals.append(obs)
                self._remember_location(portal.x, portal.y, "portal")
        
        # Update threat assessment
        self._assess_threat()
        
        self.last_update_time += 0.016  # Approximate frame time
        self.memory_access_count += 1
    
    # ========== MEMORY OPERATIONS ==========
    
    def remember_location(self, x: float, y: float, location_type: str, 
                         resources: Optional[str] = None) -> None:
        """Remember a location for future reference"""
        self._remember_location(x, y, location_type, resources)
    
    def _remember_location(self, x: float, y: float, location_type: str,
                          resources: Optional[str] = None) -> None:
        """Internal location memory"""
        key = (int(x // 64), int(y // 64))  # Chunk-based key
        
        if key not in self.known_locations:
            loc = LocationMemory(
                x=x, y=y,
                location_type=location_type,
                discovered_time=self.last_update_time,
                resources=resources
            )
            self.known_locations[key] = loc
            
            # Categorize
            if location_type == "ore_spawn" and resources:
                self.discovered_ore_types[resources].append(loc)
            elif location_type == "hazard_zone":
                self.hazard_zones.append(loc)
            elif location_type == "safe_zone":
                self.safe_zones.append(loc)
            elif location_type == "npc":
                self.npc_locations.append(loc)
            elif location_type == "portal":
                self.portal_locations.append(loc)
    
    def mark_chunk_explored(self, chunk_x: int, chunk_y: int) -> None:
        """Mark a chunk as explored"""
        self.explored_chunks.add((chunk_x, chunk_y))
    
    def is_chunk_explored(self, chunk_x: int, chunk_y: int) -> bool:
        """Check if chunk was explored"""
        return (chunk_x, chunk_y) in self.explored_chunks
    
    def get_nearest_ores(self, ore_type: Optional[str] = None, max_count: int = 5) -> List[LocationMemory]:
        """Get nearest remembered ore locations"""
        if ore_type:
            ores = self.discovered_ore_types.get(ore_type, [])
        else:
            ores = [ore for ores_list in self.discovered_ore_types.values() 
                   for ore in ores_list]
        
        # Sort by distance
        ores.sort(key=lambda o: self._distance((self.player.x, self.player.y), (o.x, o.y)))
        return ores[:max_count]
    
    def get_safe_zones(self, max_count: int = 3) -> List[LocationMemory]:
        """Get nearest safe zones"""
        zones = sorted(self.safe_zones, 
                      key=lambda z: self._distance((self.player.x, self.player.y), (z.x, z.y)))
        return zones[:max_count]
    
    def set_goal(self, goal: str, target: Optional[EntityObservation] = None) -> None:
        """Set current goal"""
        if self.current_goal != goal:
            self.current_goal = goal
            self.goal_target = target
            self.goal_changed_frame = self.memory_access_count
            self.decision_cache.clear()  # Clear cache on goal change
    
    def get_goal(self) -> Tuple[Optional[str], Optional[EntityObservation]]:
        """Get current goal and target"""
        return self.current_goal, self.goal_target
    
    # ========== THREAT ASSESSMENT ==========
    
    def _calculate_threat(self, enemy) -> float:
        """Calculate threat level of an enemy (0.0-1.0)"""
        threat = 0.0
        
        # Distance-based (closer = more threat)
        dist = self._distance((self.player.x, self.player.y), (enemy.x, enemy.y))
        if dist < 200:
            threat += (200 - dist) / 200
        
        # Health-based (healthier = more threat)
        health_ratio = enemy.health / max(1.0, enemy.max_health)
        threat += health_ratio * 0.3
        
        # Type-based (bosses are more threat)
        if "boss" in str(type(enemy).__name__).lower():
            threat += 0.5
        
        return min(1.0, threat)
    
    def _assess_threat(self) -> None:
        """Assess overall threat level from environment"""
        if not self.environment.nearby_enemies:
            self.threat_level = 0.0
            return
        
        # Average threat from all nearby enemies
        threats = [e.threat_level for e in self.environment.nearby_enemies]
        self.threat_level = sum(threats) / len(threats)
        
        self.last_threat_assessment = self.last_update_time
    
    def get_threat_level(self) -> float:
        """Get current threat level (0.0-1.0)"""
        return self.threat_level
    
    # ========== UTILITY ==========
    
    def _in_range(self, pos1: Tuple[float, float], pos2: Tuple[float, float]) -> bool:
        """Check if two positions are within scan radius"""
        return self._distance(pos1, pos2) <= self.scan_radius
    
    @staticmethod
    def _distance(pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
        """Calculate Euclidean distance"""
        dx = pos2[0] - pos1[0]
        dy = pos2[1] - pos1[1]
        return (dx * dx + dy * dy) ** 0.5
    
    def get_debug_info(self) -> Dict[str, any]:
        """Get debug information"""
        return {
            "threat_level": self.threat_level,
            "current_goal": self.current_goal,
            "nearby_enemies": len(self.environment.nearby_enemies),
            "nearby_ores": len(self.environment.nearby_ores),
            "nearby_items": len(self.environment.nearby_items),
            "nearby_npcs": len(self.environment.nearby_npcs),
            "known_locations": len(self.known_locations),
            "explored_chunks": len(self.explored_chunks),
            "memory_access_count": self.memory_access_count,
        }
