"""
World Event System
Handles environmental and world events
"""
import random
import pygame
from settings import *

class WorldEventManager:
    def __init__(self, world_manager):
        self.world_manager = world_manager
        self.active_event = None
        self.event_timer = 0.0
        
        self.time_between_events = 300.0 # 5 minutes
        self.current_idle_time = 0.0

    def update(self, dt: float, player=None, projectile_pool=None):
        if self.active_event:
            self.event_timer -= dt
            self._apply_event_effects(dt, player, projectile_pool)
            if self.event_timer <= 0:
                self.end_event()
        else:
            self.current_idle_time += dt
            if self.current_idle_time >= self.time_between_events:
                self.trigger_random_event()

    def _apply_event_effects(self, dt, player, projectile_pool):
        """Apply real-time effects based on the active event."""
        if self.active_event == "meteor_shower":
            # Spawn meteors from top
            if random.random() < 0.05:
                mx = random.uniform(player.x - 1000, player.x + 1000)
                my = player.y - 1000
                if projectile_pool:
                    projectile_pool.spawn(mx, my, 0, 1, 200, 1.0, 30, (255, 150, 0), 10, "enemy")
        
        elif self.active_event == "toxic_rain":
            # Periodic poison damage to player
            if player and random.random() < 0.01:
                player.health -= 1 * dt # Slow drain
                
        elif self.active_event == "enemy_wave":
            # Spawn extra enemies around player
            if random.random() < 0.02:
                # This would typically call world_manager.spawn_enemy()
                pass

    def trigger_random_event(self):
        # Filter events by current world
        current_world = getattr(self.world_manager, 'current_world', 'toxic_plains')
        
        event_map = {
            "toxic_plains": ["meteor_shower", "toxic_rain", "enemy_wave"],
            "crystal_desert": ["crystal_storm", "energy_surge"],
            "fungal_cave": ["spore_cloud", "cave_in"],
            "void_ruins": ["void_corruption", "reality_glitch"]
        }
        
        possible_events = event_map.get(current_world, ["enemy_wave"])
        self.active_event = random.choice(possible_events)
        self.event_timer = 60.0 # Event lasts 60 seconds
        self.current_idle_time = 0.0
        print(f"World Event Started: {self.active_event}")

    def end_event(self):
        print(f"World Event Ended: {self.active_event}")
        self.active_event = None

    def render_ui(self, surface, font):
        if not self.active_event:
            return
            
        text = f"EVENT: {self.active_event.replace('_', ' ').upper()}"
        surf = font.render(text, True, (255, 50, 50))
        surface.blit(surf, (WINDOW_WIDTH // 2 - surf.get_width() // 2, 80))

