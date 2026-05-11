"""
Performance profiling and optimization tools.
Monitors FPS, entity counts, memory usage, and provides profiling data.
"""

import pygame
import time
from typing import Dict, List
from collections import deque


class PerformanceProfiler:
    """Tracks performance metrics."""
    
    def __init__(self, max_history: int = 120):
        self.max_history = max_history
        self.fps_history: deque = deque(maxlen=max_history)
        self.frame_times: deque = deque(maxlen=max_history)
        
        self.current_fps = 0
        self.avg_fps = 0
        self.min_fps = 0
        self.max_fps = 0
        
        self.counters: Dict[str, int] = {
            'entities': 0,
            'projectiles': 0,
            'particles': 0,
            'enemies': 0,
            'bosses': 0,
        }
        
        self.frame_count = 0
        self.last_time = time.time()
    
    def update(self, clock: pygame.time.Clock) -> None:
        """Update profiler with current frame time."""
        self.frame_count += 1
        
        current_fps = clock.get_fps()
        self.fps_history.append(current_fps)
        self.current_fps = current_fps
        
        # Calculate stats
        if self.fps_history:
            self.avg_fps = sum(self.fps_history) / len(self.fps_history)
            self.min_fps = min(self.fps_history)
            self.max_fps = max(self.fps_history)
    
    def set_counter(self, name: str, value: int) -> None:
        """Set a counter value."""
        self.counters[name] = value
    
    def get_summary(self) -> Dict:
        """Get performance summary."""
        return {
            'fps': self.current_fps,
            'avg_fps': self.avg_fps,
            'min_fps': self.min_fps,
            'max_fps': self.max_fps,
            'frame_count': self.frame_count,
            'counters': self.counters.copy()
        }
    
    def render_overlay(self, surface: pygame.Surface, show_detailed: bool = False) -> None:
        """Render performance overlay."""
        font = pygame.font.SysFont(None, 20)
        
        # Main metrics
        text_lines = [
            f"FPS: {self.current_fps:.1f} (avg: {self.avg_fps:.1f})",
            f"Entities: {self.counters['entities']}",
            f"Projectiles: {self.counters['projectiles']}",
            f"Particles: {self.counters['particles']}",
        ]
        
        if show_detailed:
            text_lines.extend([
                f"Min/Max FPS: {self.min_fps:.1f} / {self.max_fps:.1f}",
                f"Enemies: {self.counters['enemies']}",
                f"Bosses: {self.counters['bosses']}",
                f"Frames: {self.frame_count}",
            ])
        
        y = 10
        for line in text_lines:
            text_surface = font.render(line, True, (0, 255, 0))
            surface.blit(text_surface, (10, y))
            y += 22


class OptimizationHints:
    """Analyzes performance and suggests optimizations."""
    
    def __init__(self):
        self.warnings: List[str] = []
        self.suggestions: List[str] = []
    
    def analyze(self, profiler: PerformanceProfiler) -> None:
        """Analyze performance data."""
        self.warnings.clear()
        self.suggestions.clear()
        
        summary = profiler.get_summary()
        
        # FPS analysis
        if summary['avg_fps'] < 30:
            self.warnings.append("WARNING: Low average FPS detected")
        
        if summary['min_fps'] < 20:
            self.warnings.append("WARNING: Frame rate drops detected")
        
        # Entity analysis
        if summary['counters']['entities'] > 500:
            self.suggestions.append("Consider entity culling (many entities)")
        
        if summary['counters']['projectiles'] > 200:
            self.suggestions.append("Consider projectile pooling optimization")
        
        if summary['counters']['particles'] > 800:
            self.suggestions.append("Consider particle culling (high particle count)")
    
    def get_report(self) -> str:
        """Get human-readable report."""
        report = "=== Performance Report ===\n"
        
        if self.warnings:
            report += "\nWarnings:\n"
            for warning in self.warnings:
                report += f"  - {warning}\n"
        
        if self.suggestions:
            report += "\nSuggestions:\n"
            for suggestion in self.suggestions:
                report += f"  - {suggestion}\n"
        
        if not self.warnings and not self.suggestions:
            report += "No issues detected!\n"
        
        return report


class EntityCuller:
    """Culls entities outside camera view."""
    
    def __init__(self, cull_margin: float = 200):
        self.cull_margin = cull_margin
    
    def should_render(self, entity_x: float, entity_y: float, entity_size: float,
                     camera_x: float, camera_y: float, 
                     screen_width: int = 1280, screen_height: int = 720) -> bool:
        """
        Check if entity should be rendered based on camera view.
        Returns True if entity is within view + margin.
        """
        # Define view bounds
        view_left = camera_x - self.cull_margin
        view_right = camera_x + screen_width + self.cull_margin
        view_top = camera_y - self.cull_margin
        view_bottom = camera_y + screen_height + self.cull_margin
        
        # Check if entity is in view
        entity_size_half = entity_size / 2
        
        if (entity_x + entity_size_half < view_left or 
            entity_x - entity_size_half > view_right or
            entity_y + entity_size_half < view_top or
            entity_y - entity_size_half > view_bottom):
            return False
        
        return True


class DebugSpawner:
    """Debug tools for testing and spawning entities."""
    
    @staticmethod
    def spawn_test_entities(play_state, count: int = 10) -> None:
        """Spawn test enemies for performance testing."""
        from entities.enemy import Enemy
        import random
        
        for _ in range(count):
            x = play_state.player.x + random.randint(-500, 500)
            y = play_state.player.y + random.randint(-500, 500)
            enemy = Enemy(x, y, "basic")
            play_state.enemies.append(enemy)
    
    @staticmethod
    def teleport_to(play_state, x: float, y: float) -> None:
        """Teleport player to position."""
        play_state.player.x = x
        play_state.player.y = y
        play_state.player.rect.center = (int(x), int(y))
    
    @staticmethod
    def trigger_slow_motion(play_state, duration: float = 1.0) -> None:
        """Trigger slow motion effect."""
        play_state.screen_effects.slow_motion.trigger(0.3, duration)
    
    @staticmethod
    def give_infinite_ammo(play_state) -> None:
        """Give infinite ammo."""
        play_state.player.disable_survival_drain = True
        play_state.player.max_oxygen = 10000
        play_state.player.oxygen = 10000
        play_state.player.max_hunger = 10000
        play_state.player.hunger = 10000
    
    @staticmethod
    def heal_player(play_state, amount: float = 100) -> None:
        """Heal player."""
        play_state.player.heal(amount)
    
    @staticmethod
    def spawn_boss(play_state, boss_type: str = "mecha_beast") -> None:
        """Spawn a boss for testing."""
        play_state.boss_manager.spawn_boss(boss_type, 
                                          play_state.player.x + 300, 
                                          play_state.player.y)
        if play_state.boss_manager.active_boss:
            play_state.bosses.append(play_state.boss_manager.active_boss)


# Global profiler instance
_profiler: PerformanceProfiler = PerformanceProfiler()

def get_profiler() -> PerformanceProfiler:
    """Get global profiler instance."""
    return _profiler
