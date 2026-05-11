"""
DFS (Depth-First Search) Module
For deep exploration and cave traversal
"""
from typing import List, Tuple, Set, Optional, Dict, Any
from collections import deque


class DFSExplorer:
    """
    Depth-First Search for exploration
    Efficiently traverses unexplored areas and caves
    """
    
    def __init__(self, world_manager, memory, tile_size: float = 64.0):
        self.world_manager = world_manager
        self.memory = memory
        self.tile_size = tile_size
        self.exploration_stack: deque = deque()
        self.current_frontier: Set[Tuple[int, int]] = set()
    
    def explore_frontier(self, start_pos: Tuple[float, float],
                        explored_tiles: Set[Tuple[int, int]],
                        max_depth: int = 50,
                        prioritize_unexplored: bool = True) -> List[Tuple[float, float]]:
        """
        Generate exploration path using DFS
        Prioritizes unexplored tiles at frontier
        """
        stx = int(start_pos[0] / self.tile_size)
        sty = int(start_pos[1] / self.tile_size)
        
        stack = [(stx, sty, [])]
        local_visited: Set[Tuple[int, int]] = set([(stx, sty)])
        frontier: List[Tuple[int, int]] = []
        
        iterations = 0
        max_iterations = 500
        
        while stack and iterations < max_iterations:
            iterations += 1
            tx, ty, path = stack.pop()
            
            # Depth limit
            if len(path) > max_depth:
                continue
            
            # If this tile is unexplored globally, return path to it
            if prioritize_unexplored and (tx, ty) not in explored_tiles:
                world_x = tx * self.tile_size + self.tile_size / 2
                world_y = ty * self.tile_size + self.tile_size / 2
                return path + [(world_x, world_y)]
            
            # Remember as frontier
            frontier.append((tx, ty))
            
            # Explore neighbors in random-ish order (DFS behavior)
            neighbors = self._get_unexplored_neighbors(tx, ty, local_visited, explored_tiles)
            
            # Prioritize edges of explored region
            neighbors_boundary = [n for n in neighbors if self._is_boundary_tile(n, explored_tiles)]
            neighbors_interior = [n for n in neighbors if n not in neighbors_boundary]
            
            # Push in reverse order to explore boundary first (LIFO)
            for nx, ny in reversed(neighbors_boundary + neighbors_interior):
                world_x = nx * self.tile_size + self.tile_size / 2
                world_y = ny * self.tile_size + self.tile_size / 2
                local_visited.add((nx, ny))
                stack.append((nx, ny, path + [(world_x, world_y)]))
        
        # If no unexplored found, return frontier path
        if frontier and len(frontier) > 0:
            tx, ty = frontier[-1]
            world_x = tx * self.tile_size + self.tile_size / 2
            world_y = ty * self.tile_size + self.tile_size / 2
            return [(world_x, world_y)]
        
        return []
    
    def explore_cave(self, start_pos: Tuple[float, float],
                    explored_tiles: Set[Tuple[int, int]],
                    max_depth: int = 100) -> List[Tuple[float, float]]:
        """
        Deep exploration of cave systems
        Uses DFS to traverse interconnected chambers
        """
        stx = int(start_pos[0] / self.tile_size)
        sty = int(start_pos[1] / self.tile_size)
        
        stack = [(stx, sty, [])]
        local_visited: Set[Tuple[int, int]] = set([(stx, sty)])
        dead_ends: List[Tuple[int, int]] = []
        
        iterations = 0
        max_iterations = 1000
        
        while stack and iterations < max_iterations:
            iterations += 1
            tx, ty, path = stack.pop()
            
            if len(path) > max_depth:
                continue
            
            # Check if this is a junction (multiple paths)
            neighbors = self._get_walkable_neighbors(tx, ty, local_visited)
            
            # Dead end
            if len(neighbors) <= 1:
                dead_ends.append((tx, ty))
            
            # Continue exploration
            for nx, ny in neighbors:
                local_visited.add((nx, ny))
                world_x = nx * self.tile_size + self.tile_size / 2
                world_y = ny * self.tile_size + self.tile_size / 2
                stack.append((nx, ny, path + [(world_x, world_y)]))
        
        # Return path to first unexplored tile or dead end
        if local_visited:
            # Find furthest unexplored point
            for tx, ty in local_visited:
                if (tx, ty) not in explored_tiles:
                    world_x = tx * self.tile_size + self.tile_size / 2
                    world_y = ty * self.tile_size + self.tile_size / 2
                    return [(world_x, world_y)]
        
        return []
    
    def backtrack_path(self, current_pos: Tuple[float, float],
                      last_junction: Optional[Tuple[float, float]] = None) -> List[Tuple[float, float]]:
        """
        Generate backtracking path for stuck situations
        Useful when exploration hits dead end
        """
        if not last_junction:
            # Just go back to start
            return [current_pos]
        
        # Move toward last junction
        path = []
        dx = last_junction[0] - current_pos[0]
        dy = last_junction[1] - current_pos[1]
        dist = (dx * dx + dy * dy) ** 0.5
        
        if dist > 0:
            step_count = int(dist / self.tile_size) + 1
            for i in range(step_count):
                t = i / step_count
                x = current_pos[0] + dx * t
                y = current_pos[1] + dy * t
                path.append((x, y))
        
        return path
    
    def get_exploration_coverage(self, explored_tiles: Set[Tuple[int, int]]) -> float:
        """Get percentage of explored tiles"""
        if not self.world_manager.chunks:
            return 0.0
        
        total_tiles = len(self.world_manager.chunks) * 32 * 32
        explored = len(explored_tiles)
        
        return (explored / total_tiles) * 100.0 if total_tiles > 0 else 0.0
    
    def get_next_exploration_target(self, current_pos: Tuple[float, float],
                                   explored_tiles: Set[Tuple[int, int]],
                                   memory) -> Optional[Tuple[float, float]]:
        """
        Get next strategic exploration target
        Considers frontier, chunks, and memory
        """
        # Priority 1: Frontier tiles in current region
        frontier_targets = memory.get_frontier_targets(count=3)
        if frontier_targets:
            tx, ty = frontier_targets[0]
            return (tx * self.tile_size + self.tile_size / 2,
                   ty * self.tile_size + self.tile_size / 2)
        
        # Priority 2: Unexplored chunks
        current_chunk_x = int(current_pos[0] / (32 * self.tile_size))
        current_chunk_y = int(current_pos[1] / (32 * self.tile_size))
        
        unexplored_chunks = memory.get_unexplored_chunks(
            current_chunk_x, current_chunk_y, search_radius=3
        )
        
        if unexplored_chunks:
            cx, cy = unexplored_chunks[0]
            x = cx * 32 * self.tile_size + 16 * self.tile_size
            y = cy * 32 * self.tile_size + 16 * self.tile_size
            return (x, y)
        
        # Priority 3: Search wider
        unexplored_chunks = memory.get_unexplored_chunks(
            current_chunk_x, current_chunk_y, search_radius=7
        )
        
        if unexplored_chunks:
            cx, cy = unexplored_chunks[0]
            x = cx * 32 * self.tile_size + 16 * self.tile_size
            y = cy * 32 * self.tile_size + 16 * self.tile_size
            return (x, y)
        
        return None
    
    def _get_unexplored_neighbors(self, tx: int, ty: int,
                                 local_visited: Set[Tuple[int, int]],
                                 global_explored: Set[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """Get walkable neighbors that haven't been visited locally"""
        neighbors = []
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0),
                       (1, 1), (-1, -1), (1, -1), (-1, 1)]:
            nx, ny = tx + dx, ty + dy
            if (nx, ny) not in local_visited and self._is_walkable(nx, ny):
                neighbors.append((nx, ny))
        return neighbors
    
    def _get_walkable_neighbors(self, tx: int, ty: int,
                               visited: Set[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """Get all walkable unvisited neighbors"""
        neighbors = []
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0),
                       (1, 1), (-1, -1), (1, -1), (-1, 1)]:
            nx, ny = tx + dx, ty + dy
            if (nx, ny) not in visited and self._is_walkable(nx, ny):
                neighbors.append((nx, ny))
        return neighbors
    
    def _is_boundary_tile(self, tile: Tuple[int, int],
                         explored: Set[Tuple[int, int]]) -> bool:
        """Check if tile is at boundary of explored region"""
        tx, ty = tile
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = tx + dx, ty + dy
            if (nx, ny) not in explored:
                return True
        return False
    
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
            "exploration_stack_size": len(self.exploration_stack),
            "current_frontier_size": len(self.current_frontier),
        }
