"""
Navigation Module for AI
Advanced pathfinding with weighted costs, dynamic updates, path smoothing
"""
from typing import List, Tuple, Optional, Set, Dict
from enum import Enum
import math


class TerrainType(Enum):
    """Terrain types with different movement costs"""
    SAFE = 1.0
    DIFFICULT = 3.0
    HAZARDOUS = 5.0
    IMPASSABLE = float('inf')


class NavigationController:
    """
    High-level navigation system
    Combines pathfinding with real-time adjustments
    """
    
    def __init__(self, pathfinding, world_manager, tile_size: float = 64.0):
        self.pathfinding = pathfinding
        self.world_manager = world_manager
        self.tile_size = tile_size
        
        # Current path
        self.current_path: List[Tuple[float, float]] = []
        self.path_index: int = 0
        self.path_dirty: bool = False
        self.path_recalc_cooldown: float = 0.0
        self.path_recalc_interval: float = 1.0  # Recalc every 1 second
        
        # Performance
        self.last_recalc_pos: Tuple[float, float] = (0.0, 0.0)
        self.min_recalc_distance: float = 100.0
        self.path_cache: Dict = {}
        
        # Terrain knowledge
        self.terrain_costs: Dict[Tuple[int, int], float] = {}
        self.hazard_zones: List[Tuple[float, float, float]] = []  # (x, y, radius)
        self.enemy_zones: List[Tuple[float, float, float]] = []
    
    def set_path(self, path: List[Tuple[float, float]]) -> None:
        """Set a new path"""
        self.current_path = path
        self.path_index = 0
        self.path_dirty = False
    
    def get_next_waypoint(self) -> Optional[Tuple[float, float]]:
        """Get next waypoint in path"""
        if not self.current_path or self.path_index >= len(self.current_path):
            return None
        return self.current_path[self.path_index]
    
    def advance_waypoint(self) -> None:
        """Move to next waypoint"""
        self.path_index += 1
    
    def has_reached_waypoint(self, current_pos: Tuple[float, float], 
                            threshold: float = 15.0) -> bool:
        """Check if reached current waypoint"""
        waypoint = self.get_next_waypoint()
        if not waypoint:
            return False
        
        dist = self._distance(current_pos, waypoint)
        return dist <= threshold
    
    def is_path_valid(self, current_pos: Tuple[float, float]) -> bool:
        """Check if current path is still valid"""
        # Path invalid if we deviated significantly
        if self.path_index < len(self.current_path):
            target = self.current_path[self.path_index]
            deviation = self._distance(current_pos, target)
            return deviation < 100.0
        return len(self.current_path) > 0
    
    def should_recalculate_path(self, current_pos: Tuple[float, float]) -> bool:
        """Check if path needs recalculation"""
        # Distance moved
        dist_moved = self._distance(current_pos, self.last_recalc_pos)
        
        # Cooldown check
        if self.path_recalc_cooldown > 0:
            return False
        
        # Significant movement
        if dist_moved > self.min_recalc_distance:
            return True
        
        # Path validity
        if not self.is_path_valid(current_pos):
            return True
        
        return False
    
    def update_path(self, current_pos: Tuple[float, float], 
                   goal_pos: Tuple[float, float],
                   avoid_hazards: bool = True,
                   avoid_enemies: bool = False,
                   dt: float = 0.016) -> bool:
        """
        Update path with weighted terrain costs
        Returns True if new path calculated
        """
        self.path_recalc_cooldown -= dt
        
        if not self.should_recalculate_path(current_pos):
            return False
        
        # Build weighted pathfinding request
        terrain_weights = self._calculate_terrain_weights(avoid_hazards, avoid_enemies)
        
        # Use A* with weighted costs
        path = self.pathfinding.astar_weighted(
            current_pos, goal_pos,
            terrain_weights=terrain_weights
        )
        
        if path:
            # Smooth path
            path = self._smooth_path(path)
            self.set_path(path)
            self.last_recalc_pos = current_pos
            self.path_recalc_cooldown = self.path_recalc_interval
            return True
        
        return False
    
    def _calculate_terrain_weights(self, avoid_hazards: bool, 
                                  avoid_enemies: bool) -> Dict[Tuple[int, int], float]:
        """Calculate terrain movement costs"""
        weights = {}
        
        # Base terrain costs
        for chunk_pos, chunk in self.world_manager.chunks.items():
            for ty in range(32):
                for tx in range(32):
                    if chunk.grid_data[ty][tx] != 0:  # Obstacle
                        weights[(chunk_pos[0] * 32 + tx, chunk_pos[1] * 32 + ty)] = float('inf')
        
        # Hazard penalties
        if avoid_hazards:
            for hx, hy, radius in self.hazard_zones:
                # Apply gradient cost around hazard
                for angle in range(0, 360, 45):
                    rad = math.radians(angle)
                    for dist in range(0, int(radius) + 50, 10):
                        x = hx + math.cos(rad) * dist
                        y = hy + math.sin(rad) * dist
                        tx, ty = int(x / self.tile_size), int(y / self.tile_size)
                        cost = 1.0 + (1.0 - (dist / (radius + 50))) * 4.0
                        key = (tx, ty)
                        weights[key] = max(weights.get(key, 1.0), cost)
        
        # Enemy zone penalties
        if avoid_enemies:
            for ex, ey, radius in self.enemy_zones:
                for angle in range(0, 360, 45):
                    rad = math.radians(angle)
                    for dist in range(0, int(radius) + 100, 10):
                        x = ex + math.cos(rad) * dist
                        y = ey + math.sin(rad) * dist
                        tx, ty = int(x / self.tile_size), int(y / self.tile_size)
                        cost = 1.0 + (1.0 - (dist / (radius + 100))) * 3.0
                        key = (tx, ty)
                        weights[key] = max(weights.get(key, 1.0), cost)
        
        return weights
    
    def _smooth_path(self, path: List[Tuple[float, float]], 
                    iterations: int = 2) -> List[Tuple[float, float]]:
        """Smooth path to reduce sharp turns"""
        if len(path) < 3:
            return path
        
        for _ in range(iterations):
            smoothed = [path[0]]
            for i in range(1, len(path) - 1):
                prev = path[i - 1]
                curr = path[i]
                next_ = path[i + 1]
                
                # Check if we can skip current waypoint
                if self._can_skip_waypoint(prev, curr, next_):
                    continue
                
                # Smooth by averaging
                avg_x = (prev[0] + curr[0] + next_[0]) / 3
                avg_y = (prev[1] + curr[1] + next_[1]) / 3
                smoothed.append((avg_x, avg_y))
            
            smoothed.append(path[-1])
            path = smoothed
        
        return path
    
    def _can_skip_waypoint(self, prev: Tuple[float, float], 
                          curr: Tuple[float, float],
                          next_: Tuple[float, float],
                          skip_threshold: float = 10.0) -> bool:
        """Check if waypoint can be skipped (path smoothing)"""
        # Simple check: if waypoint is close to line between prev and next
        # Calculate perpendicular distance
        dist = self._point_to_line_distance(curr, prev, next_)
        return dist < skip_threshold
    
    def add_hazard_zone(self, x: float, y: float, radius: float) -> None:
        """Add hazard zone for avoidance"""
        self.hazard_zones.append((x, y, radius))
    
    def add_enemy_zone(self, x: float, y: float, radius: float) -> None:
        """Add enemy concentration zone for avoidance"""
        self.enemy_zones.append((x, y, radius))
    
    def clear_dynamic_zones(self) -> None:
        """Clear dynamic hazard/enemy zones (update each frame)"""
        self.hazard_zones.clear()
        self.enemy_zones.clear()
    
    @staticmethod
    def _distance(pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
        """Euclidean distance"""
        dx = pos2[0] - pos1[0]
        dy = pos2[1] - pos1[1]
        return math.sqrt(dx * dx + dy * dy)
    
    @staticmethod
    def _point_to_line_distance(point: Tuple[float, float],
                               line_start: Tuple[float, float],
                               line_end: Tuple[float, float]) -> float:
        """Distance from point to line segment"""
        x, y = point
        x1, y1 = line_start
        x2, y2 = line_end
        
        # Vector from start to end
        dx = x2 - x1
        dy = y2 - y1
        
        # Length squared
        len_sq = dx * dx + dy * dy
        
        if len_sq == 0:
            return NavigationController._distance(point, line_start)
        
        # Parameter t for closest point on line
        t = max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / len_sq))
        
        # Closest point
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        
        # Distance to closest point
        return NavigationController._distance(point, (closest_x, closest_y))
    
    def get_debug_info(self) -> Dict[str, any]:
        """Get debug information"""
        return {
            "path_length": len(self.current_path),
            "path_index": self.path_index,
            "path_valid": self.is_path_valid(self.last_recalc_pos) if self.current_path else False,
            "hazard_zones": len(self.hazard_zones),
            "enemy_zones": len(self.enemy_zones),
        }
