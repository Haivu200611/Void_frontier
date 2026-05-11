"""
BFS (Breadth-First Search) Module
For nearby resource scanning and local path finding
"""
from collections import deque
from typing import List, Tuple, Callable, Optional, Set, Dict, Any
from enum import Enum


class ScanType(Enum):
    """Types of BFS scans"""
    NEAREST_ORE = "nearest_ore"
    NEAREST_LOOT = "nearest_loot"
    NEAREST_NPC = "nearest_npc"
    NEAREST_HAZARD = "nearest_hazard"
    NEAREST_SAFE_ZONE = "nearest_safe_zone"
    NEAREST_OXYGEN = "nearest_oxygen"
    NEAREST_ENEMY = "nearest_enemy"


class BFSScanner:
    """
    Breadth-First Search for local resource scanning
    Optimized for finding nearest targets
    """
    
    def __init__(self, world_manager, tile_size: float = 64.0):
        self.world_manager = world_manager
        self.tile_size = tile_size
        self.search_history: Dict[str, Tuple[float, float]] = {}
    
    def find_nearest(self, start_pos: Tuple[float, float],
                    predicate: Callable,
                    max_depth: int = 25,
                    avoid_obstacles: bool = True) -> Optional[Tuple[List[Tuple[float, float]], float]]:
        """
        Find nearest target using BFS
        
        Args:
            start_pos: Starting position (world coords)
            predicate: Function(x, y) -> bool that identifies target
            max_depth: Max BFS depth (in tiles)
            avoid_obstacles: Whether to check walkability
        
        Returns:
            Tuple of (path, distance) or None if not found
        """
        stx = int(start_pos[0] / self.tile_size)
        sty = int(start_pos[1] / self.tile_size)
        
        queue = deque([(stx, sty, [])])
        visited: Set[Tuple[int, int]] = set([(stx, sty)])
        depth_visited = 0
        
        while queue:
            tx, ty, path = queue.popleft()
            
            # Check depth limit
            if len(path) > max_depth:
                continue
            
            # Check predicate
            world_x = tx * self.tile_size + self.tile_size / 2
            world_y = ty * self.tile_size + self.tile_size / 2
            
            if predicate(world_x, world_y):
                distance = len(path) * self.tile_size
                full_path = path + [(world_x, world_y)]
                return full_path, distance
            
            # Explore neighbors (4-connectivity for efficiency)
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = tx + dx, ty + dy
                
                if (nx, ny) in visited:
                    continue
                
                if avoid_obstacles and not self._is_walkable(nx, ny):
                    continue
                
                visited.add((nx, ny))
                waypoint = (world_x + dx * self.tile_size, 
                           world_y + dy * self.tile_size)
                queue.append((nx, ny, path + [waypoint]))
                depth_visited += 1
        
        return None
    
    def find_all(self, start_pos: Tuple[float, float],
                predicate: Callable,
                max_depth: int = 20) -> List[Tuple[List[Tuple[float, float]], float]]:
        """
        Find all targets within range (sorted by distance)
        """
        stx = int(start_pos[0] / self.tile_size)
        sty = int(start_pos[1] / self.tile_size)
        
        queue = deque([(stx, sty, [])])
        visited: Set[Tuple[int, int]] = set([(stx, sty)])
        results: List[Tuple[List[Tuple[float, float]], float]] = []
        
        while queue:
            tx, ty, path = queue.popleft()
            
            if len(path) > max_depth:
                continue
            
            world_x = tx * self.tile_size + self.tile_size / 2
            world_y = ty * self.tile_size + self.tile_size / 2
            
            if predicate(world_x, world_y):
                distance = len(path) * self.tile_size
                full_path = path + [(world_x, world_y)]
                results.append((full_path, distance))
            
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = tx + dx, ty + dy
                
                if (nx, ny) not in visited and self._is_walkable(nx, ny):
                    visited.add((nx, ny))
                    waypoint = (world_x + dx * self.tile_size,
                               world_y + dy * self.tile_size)
                    queue.append((nx, ny, path + [waypoint]))
        
        # Sort by distance
        results.sort(key=lambda r: r[1])
        return results
    
    def scan_ores(self, start_pos: Tuple[float, float],
                 nearby_ores: List,
                 max_count: int = 5) -> Optional[List[Tuple[float, float]]]:
        """Scan for nearest ore(s)"""
        def ore_predicate(x, y):
            for ore in nearby_ores:
                if abs(ore.x - x) < 40 and abs(ore.y - y) < 40:
                    return True
            return False
        
        result = self.find_nearest(start_pos, ore_predicate, max_depth=20)
        return result[0] if result else None
    
    def scan_loot(self, start_pos: Tuple[float, float],
                 nearby_items: List,
                 max_count: int = 5) -> Optional[List[Tuple[float, float]]]:
        """Scan for nearest loot"""
        def loot_predicate(x, y):
            for item in nearby_items:
                if abs(item.x - x) < 40 and abs(item.y - y) < 40:
                    return True
            return False
        
        result = self.find_nearest(start_pos, loot_predicate, max_depth=20)
        return result[0] if result else None
    
    def scan_npc(self, start_pos: Tuple[float, float],
                nearby_npcs: List) -> Optional[List[Tuple[float, float]]]:
        """Scan for nearest NPC (trader)"""
        def npc_predicate(x, y):
            for npc in nearby_npcs:
                if abs(npc.x - x) < 50 and abs(npc.y - y) < 50:
                    return True
            return False
        
        result = self.find_nearest(start_pos, npc_predicate, max_depth=25)
        return result[0] if result else None
    
    def scan_oxygen_source(self, start_pos: Tuple[float, float],
                          safe_zones: List[Tuple[float, float]]) -> Optional[List[Tuple[float, float]]]:
        """Scan for oxygen source (safe zone)"""
        def oxygen_predicate(x, y):
            for zx, zy in safe_zones:
                if abs(zx - x) < 60 and abs(zy - y) < 60:
                    return True
            return False
        
        result = self.find_nearest(start_pos, oxygen_predicate, max_depth=30)
        return result[0] if result else None
    
    def get_reachable_area(self, start_pos: Tuple[float, float],
                          max_depth: int = 15) -> Set[Tuple[int, int]]:
        """Get all reachable tiles within depth"""
        stx = int(start_pos[0] / self.tile_size)
        sty = int(start_pos[1] / self.tile_size)
        
        queue = deque([(stx, sty, 0)])
        reachable: Set[Tuple[int, int]] = set([(stx, sty)])
        
        while queue:
            tx, ty, depth = queue.popleft()
            
            if depth >= max_depth:
                continue
            
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = tx + dx, ty + dy
                
                if (nx, ny) not in reachable and self._is_walkable(nx, ny):
                    reachable.add((nx, ny))
                    queue.append((nx, ny, depth + 1))
        
        return reachable
    
    def flood_fill(self, start_pos: Tuple[float, float],
                  max_tiles: int = 100) -> Set[Tuple[int, int]]:
        """Flood fill to find connected walkable area"""
        stx = int(start_pos[0] / self.tile_size)
        sty = int(start_pos[1] / self.tile_size)
        
        queue = deque([(stx, sty)])
        filled: Set[Tuple[int, int]] = set([(stx, sty)])
        
        while queue and len(filled) < max_tiles:
            tx, ty = queue.popleft()
            
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0),
                          (1, 1), (-1, -1), (1, -1), (-1, 1)]:
                nx, ny = tx + dx, ty + dy
                
                if (nx, ny) not in filled and self._is_walkable(nx, ny):
                    filled.add((nx, ny))
                    queue.append((nx, ny))
        
        return filled
    
    def _is_walkable(self, tx: int, ty: int) -> bool:
        """Check if tile is walkable"""
        chunk_x = tx // 32
        chunk_y = ty // 32
        local_x = tx % 32
        local_y = ty % 32
        
        if (chunk_x, chunk_y) not in self.world_manager.chunks:
            return False
        
        chunk = self.world_manager.chunks[(chunk_x, chunk_y)]
        if local_y < 0 or local_y >= 32 or local_x < 0 or local_x >= 32:
            return False
        
        return chunk.grid_data[local_y][local_x] == 0
    
    def get_debug_info(self) -> Dict[str, any]:
        """Get debug information"""
        return {
            "search_history_size": len(self.search_history),
        }
