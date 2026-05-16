from ai.pathfinding import Pathfinding
from ai.heuristic import HeuristicSystem
from settings import *


class AutoPlayerController:
    def __init__(self, player, world_manager):
        self.player = player
        self.pathfinding = Pathfinding(world_manager)
        self.heuristic = HeuristicSystem(player, world_manager)

        self.global_visited_tiles = set()
        self.current_path = []

    def update(self, dt, enemies, items, in_hazard=False):
        self.global_visited_tiles.add((int(self.player.x // TILE_SIZE), int(self.player.y // TILE_SIZE)))

        state = self.heuristic.evaluate(enemies, items, in_hazard=in_hazard)

        if state == "ATTACK" and enemies:
            nearest = min(enemies, key=lambda e: ((e.x - self.player.x) ** 2 + (e.y - self.player.y) ** 2) ** 0.5)
            dist = ((nearest.x - self.player.x) ** 2 + (nearest.y - self.player.y) ** 2) ** 0.5

            if dist > 80:
                self.current_path = self.pathfinding.astar((self.player.x, self.player.y), (nearest.x, nearest.y))
                self.follow_path()
            else:
                self.player.velocity_x = 0
                self.player.velocity_y = 0

        elif state in ["EXPLORE", "LOOT", "FIND_OXYGEN", "FIND_FOOD"]:
            if not self.current_path:
                self.current_path = self.pathfinding.dfs_explore((self.player.x, self.player.y), self.global_visited_tiles)
            self.follow_path()

        elif state == "FLEE":
            # Move toward unexplored path quickly when pressured.
            if not self.current_path:
                self.current_path = self.pathfinding.dfs_explore((self.player.x, self.player.y), self.global_visited_tiles)
            self.follow_path(speed_multiplier=1.2)

    def follow_path(self, speed_multiplier=1.0):
        if not self.current_path:
            self.player.velocity_x = 0
            self.player.velocity_y = 0
            return

        tx, ty = self.current_path[0]
        dist = ((tx - self.player.x) ** 2 + (ty - self.player.y) ** 2) ** 0.5

        if dist < 10:
            self.current_path.pop(0)
            return

        dir_x, dir_y = tx - self.player.x, ty - self.player.y
        speed = self.player.speed * speed_multiplier
        self.player.velocity_x = (dir_x / dist) * speed
        self.player.velocity_y = (dir_y / dist) * speed
