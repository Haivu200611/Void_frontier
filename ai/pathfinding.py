import heapq
from collections import deque
from settings import TILE_SIZE

class Pathfinding:
    def __init__(self, world_manager):
        self.world_manager = world_manager
        
    def is_walkable(self, tx, ty):
        cx, cy = tx // 32, ty // 32
        lx, ly = tx % 32, ty % 32
        if (cx, cy) in self.world_manager.chunks:
            return self.world_manager.chunks[(cx, cy)].grid_data[ly][lx] == 0
        return False
        
    def astar(self, start_pos, goal_pos):
        stx, sty = int(start_pos[0] // TILE_SIZE), int(start_pos[1] // TILE_SIZE)
        gtx, gty = int(goal_pos[0] // TILE_SIZE), int(goal_pos[1] // TILE_SIZE)
        
        open_set = []
        heapq.heappush(open_set, (0, (stx, sty)))
        came_from = {}
        g_score = {(stx, sty): 0}
        
        # Limit iterations for performance
        iterations = 0
        max_iterations = 500
        
        while open_set and iterations < max_iterations:
            iterations += 1
            _, current = heapq.heappop(open_set)
            
            if current == (gtx, gty) or ((current[0]-gtx)**2 + (current[1]-gty)**2)**0.5 < 2:
                path = []
                while current in came_from:
                    path.append((current[0] * TILE_SIZE + TILE_SIZE/2, current[1] * TILE_SIZE + TILE_SIZE/2))
                    current = came_from[current]
                return path[::-1]
                
            for dx, dy in [(0,1), (1,0), (0,-1), (-1,0), (1,1), (-1,-1), (1,-1), (-1,1)]:
                nx, ny = current[0] + dx, current[1] + dy
                if not self.is_walkable(nx, ny): continue
                
                tentative_g = g_score[current] + ((dx**2 + dy**2)**0.5)
                if (nx, ny) not in g_score or tentative_g < g_score[(nx, ny)]:
                    came_from[(nx, ny)] = current
                    g_score[(nx, ny)] = tentative_g
                    f_score = tentative_g + ((nx - gtx)**2 + (ny - gty)**2)**0.5
                    heapq.heappush(open_set, (f_score, (nx, ny)))
                    
        return []
        
    def bfs_find_nearest(self, start_pos, target_predicate, max_depth=30):
        stx, sty = int(start_pos[0] // TILE_SIZE), int(start_pos[1] // TILE_SIZE)
        queue = deque([(stx, sty, [])])
        visited = set([(stx, sty)])
        
        while queue:
            cx, cy, path = queue.popleft()
            
            if len(path) > max_depth:
                continue
                
            if target_predicate(cx * TILE_SIZE, cy * TILE_SIZE):
                return path
                
            for dx, dy in [(0,1), (1,0), (0,-1), (-1,0)]:
                nx, ny = cx + dx, cy + dy
                if (nx, ny) not in visited and self.is_walkable(nx, ny):
                    visited.add((nx, ny))
                    queue.append((nx, ny, path + [(nx * TILE_SIZE + TILE_SIZE/2, ny * TILE_SIZE + TILE_SIZE/2)]))
        return []
        
    def dfs_explore(self, start_pos, global_visited_tiles, max_depth=50):
        stx, sty = int(start_pos[0] // TILE_SIZE), int(start_pos[1] // TILE_SIZE)
        stack = [(stx, sty, [])]
        local_visited = set([(stx, sty)])
        
        while stack:
            cx, cy, path = stack.pop()
            
            if len(path) > max_depth:
                continue
                
            if (cx, cy) not in global_visited_tiles:
                return path
                
            for dx, dy in [(0,1), (1,0), (0,-1), (-1,0)]:
                nx, ny = cx + dx, cy + dy
                if (nx, ny) not in local_visited and self.is_walkable(nx, ny):
                    local_visited.add((nx, ny))
                    stack.append((nx, ny, path + [(nx * TILE_SIZE + TILE_SIZE/2, ny * TILE_SIZE + TILE_SIZE/2)]))
        return []
    
    def astar_weighted(self, start_pos, goal_pos, terrain_weights=None):
        """
        A* pathfinding with weighted terrain costs
        terrain_weights: dict of (tile_x, tile_y) -> cost multiplier
        """
        stx, sty = int(start_pos[0] // TILE_SIZE), int(start_pos[1] // TILE_SIZE)
        gtx, gty = int(goal_pos[0] // TILE_SIZE), int(goal_pos[1] // TILE_SIZE)
        
        if terrain_weights is None:
            terrain_weights = {}
        
        open_set = []
        heapq.heappush(open_set, (0, (stx, sty)))
        came_from = {}
        g_score = {(stx, sty): 0}
        
        iterations = 0
        max_iterations = 1000
        
        while open_set and iterations < max_iterations:
            iterations += 1
            _, current = heapq.heappop(open_set)
            
            if current == (gtx, gty) or ((current[0]-gtx)**2 + (current[1]-gty)**2)**0.5 < 2:
                path = []
                while current in came_from:
                    path.append((current[0] * TILE_SIZE + TILE_SIZE/2, current[1] * TILE_SIZE + TILE_SIZE/2))
                    current = came_from[current]
                return path[::-1]
            
            for dx, dy in [(0,1), (1,0), (0,-1), (-1,0), (1,1), (-1,-1), (1,-1), (-1,1)]:
                nx, ny = current[0] + dx, current[1] + dy
                if not self.is_walkable(nx, ny):
                    continue
                
                # Get terrain weight
                weight = terrain_weights.get((nx, ny), 1.0)
                if weight == float('inf'):  # Impassable
                    continue
                
                move_cost = ((dx**2 + dy**2)**0.5) * weight
                tentative_g = g_score[current] + move_cost
                
                if (nx, ny) not in g_score or tentative_g < g_score[(nx, ny)]:
                    came_from[(nx, ny)] = current
                    g_score[(nx, ny)] = tentative_g
                    f_score = tentative_g + ((nx - gtx)**2 + (ny - gty)**2)**0.5
                    heapq.heappush(open_set, (f_score, (nx, ny)))
        
        return []
