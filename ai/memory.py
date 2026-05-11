"""
AI Memory System
Tracks exploration, discovered locations, learned patterns
"""
from typing import Set, Dict, List, Tuple, Optional
from enum import Enum
import time


class ExplorationPhase(Enum):
    """Phases of world exploration"""
    STARTING = "starting"
    LOCAL = "local"
    REGIONAL = "regional"
    DEEP = "deep"
    COMPLETE = "complete"


class AIMemory:
    """
    Long-term memory for AI
    
    Tracks:
    - Explored tiles/chunks
    - Discovered resources
    - Hazard patterns
    - Safe routes
    - Enemy spawning patterns
    """
    
    def __init__(self, tile_size: float = 64.0):
        self.tile_size = tile_size
        
        # Exploration tracking (by tile)
        self.explored_tiles: Set[Tuple[int, int]] = set()
        self.visited_chunks: Set[Tuple[int, int]] = set()
        self.frontier_tiles: Set[Tuple[int, int]] = set()  # Tiles at exploration boundary
        
        # Resource memory
        self.ore_locations: Dict[str, List[Tuple[float, float]]] = {
            "iron": [],
            "crystal": [],
            "toxic": [],
            "void": [],
        }
        self.ore_exhausted: Set[Tuple[int, int]] = set()  # Tiles where ore was mined
        
        # Hazard memory
        self.hazard_zones: Dict[str, List[Tuple[float, float, float]]] = {}  # type -> [(x, y, radius), ...]
        self.safe_corridors: List[Tuple[Tuple[float, float], Tuple[float, float]]] = []  # Safe paths
        
        # Enemy patterns
        self.enemy_spawn_zones: List[Tuple[float, float, float]] = []  # (x, y, radius)
        self.enemy_patrol_patterns: Dict[int, List[Tuple[float, float]]] = {}  # enemy_id -> path
        
        # Temporal data
        self.last_exploration_update: float = 0.0
        self.exploration_phase: ExplorationPhase = ExplorationPhase.STARTING
        self.total_explored_area: float = 0.0  # Approximate sq units
        
        # Patterns
        self.repeated_locations: Dict[Tuple[int, int], int] = {}  # Location -> visit count
        self.stuck_counter: int = 0
        self.stuck_location: Optional[Tuple[float, float]] = None
        self.stuck_threshold: int = 120  # frames before considered stuck
    
    def mark_tile_explored(self, x: float, y: float) -> None:
        """Mark a tile as explored"""
        tile_x = int(x / self.tile_size)
        tile_y = int(y / self.tile_size)
        key = (tile_x, tile_y)
        
        if key not in self.explored_tiles:
            self.explored_tiles.add(key)
            self.total_explored_area += self.tile_size * self.tile_size
            self._update_frontier(tile_x, tile_y)
    
    def _update_frontier(self, tx: int, ty: int) -> None:
        """Update exploration frontier"""
        key = (tx, ty)
        
        # Check neighbors
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0), 
                       (1, 1), (-1, -1), (1, -1), (-1, 1)]:
            neighbor = (tx + dx, ty + dy)
            if neighbor not in self.explored_tiles:
                self.frontier_tiles.add(neighbor)
        
        # Remove from frontier if explored
        self.frontier_tiles.discard(key)
    
    def mark_chunk_visited(self, chunk_x: int, chunk_y: int) -> None:
        """Mark chunk as visited"""
        self.visited_chunks.add((chunk_x, chunk_y))
        self._update_exploration_phase()
    
    def get_unexplored_chunks(self, center_chunk_x: int, center_chunk_y: int, 
                             search_radius: int = 5) -> List[Tuple[int, int]]:
        """Get unexplored chunks near center"""
        unexplored = []
        for dx in range(-search_radius, search_radius + 1):
            for dy in range(-search_radius, search_radius + 1):
                chunk = (center_chunk_x + dx, center_chunk_y + dy)
                if chunk not in self.visited_chunks:
                    unexplored.append(chunk)
        
        return sorted(unexplored, 
                     key=lambda c: (abs(c[0] - center_chunk_x) + 
                                  abs(c[1] - center_chunk_y)))
    
    def remember_ore(self, ore_type: str, x: float, y: float) -> None:
        """Remember ore location"""
        if ore_type in self.ore_locations:
            # Avoid duplicates (same location)
            for ex, ey in self.ore_locations[ore_type]:
                if abs(ex - x) < 32 and abs(ey - y) < 32:
                    return
            self.ore_locations[ore_type].append((x, y))
    
    def mark_ore_exhausted(self, x: float, y: float) -> None:
        """Mark ore location as exhausted"""
        tx = int(x / self.tile_size)
        ty = int(y / self.tile_size)
        self.ore_exhausted.add((tx, ty))
    
    def get_nearest_ore(self, player_x: float, player_y: float, 
                       ore_type: Optional[str] = None, 
                       exclude_exhausted: bool = True) -> Optional[Tuple[float, float]]:
        """Get nearest ore location from memory"""
        candidates = []
        
        if ore_type:
            candidates = self.ore_locations.get(ore_type, [])
        else:
            for ores in self.ore_locations.values():
                candidates.extend(ores)
        
        if exclude_exhausted:
            candidates = [
                (x, y) for x, y in candidates
                if (int(x / self.tile_size), int(y / self.tile_size)) not in self.ore_exhausted
            ]
        
        if not candidates:
            return None
        
        # Find nearest
        nearest = min(candidates, 
                     key=lambda pos: (pos[0] - player_x) ** 2 + (pos[1] - player_y) ** 2)
        return nearest
    
    def remember_hazard_zone(self, zone_type: str, x: float, y: float, radius: float) -> None:
        """Remember hazard zone"""
        if zone_type not in self.hazard_zones:
            self.hazard_zones[zone_type] = []
        
        # Check for duplicates
        for hx, hy, hr in self.hazard_zones[zone_type]:
            if abs(hx - x) < radius and abs(hy - y) < radius:
                return  # Already known
        
        self.hazard_zones[zone_type].append((x, y, radius))
    
    def is_near_hazard(self, x: float, y: float) -> Tuple[bool, Optional[str]]:
        """Check if position is near a remembered hazard"""
        for zone_type, zones in self.hazard_zones.items():
            for hx, hy, radius in zones:
                dist = ((x - hx) ** 2 + (y - hy) ** 2) ** 0.5
                if dist < radius + 50:  # Add buffer
                    return True, zone_type
        return False, None
    
    def remember_enemy_pattern(self, enemy_id: int, positions: List[Tuple[float, float]]) -> None:
        """Remember enemy patrol pattern"""
        self.enemy_patrol_patterns[enemy_id] = positions
    
    def track_stuck(self, x: float, y: float) -> bool:
        """Track if AI is stuck in same location"""
        current_pos = (int(x), int(y))
        
        if current_pos == self.stuck_location:
            self.stuck_counter += 1
        else:
            self.stuck_counter = 0
            self.stuck_location = current_pos
        
        return self.stuck_counter > self.stuck_threshold
    
    def reset_stuck(self) -> None:
        """Reset stuck tracker"""
        self.stuck_counter = 0
        self.stuck_location = None
    
    def _update_exploration_phase(self) -> None:
        """Update exploration phase based on progress"""
        chunk_count = len(self.visited_chunks)
        
        if chunk_count < 5:
            self.exploration_phase = ExplorationPhase.STARTING
        elif chunk_count < 20:
            self.exploration_phase = ExplorationPhase.LOCAL
        elif chunk_count < 50:
            self.exploration_phase = ExplorationPhase.REGIONAL
        elif chunk_count < 100:
            self.exploration_phase = ExplorationPhase.DEEP
        else:
            self.exploration_phase = ExplorationPhase.COMPLETE
    
    def get_exploration_status(self) -> Dict[str, any]:
        """Get exploration status"""
        return {
            "phase": self.exploration_phase.value,
            "chunks_visited": len(self.visited_chunks),
            "tiles_explored": len(self.explored_tiles),
            "frontier_size": len(self.frontier_tiles),
            "total_area": self.total_explored_area,
            "ores_discovered": {k: len(v) for k, v in self.ore_locations.items()},
            "hazards_known": {k: len(v) for k, v in self.hazard_zones.items()},
        }
    
    def get_frontier_targets(self, count: int = 5) -> List[Tuple[int, int]]:
        """Get frontier tiles to explore next"""
        return sorted(list(self.frontier_tiles))[:count]
    
    def clear_exploration_memory(self) -> None:
        """Clear all exploration data (fresh start)"""
        self.explored_tiles.clear()
        self.visited_chunks.clear()
        self.frontier_tiles.clear()
        self.total_explored_area = 0.0
        self.exploration_phase = ExplorationPhase.STARTING
