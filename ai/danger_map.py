"""
Danger Map System
Real-time assessment of environmental danger levels
Influences pathfinding and decision making
"""
from typing import Dict, List, Tuple, Optional, Set, Any
import math


class DangerZone:
    """Represents a dangerous area"""
    def __init__(self, x: float, y: float, radius: float, 
                 danger_type: str, severity: float = 1.0):
        self.x = x
        self.y = y
        self.radius = radius
        self.danger_type = danger_type  # "enemy", "hazard", "boss", "projectile"
        self.severity = severity  # 0.0-1.0
        self.lifetime = 0.0
        self.max_lifetime = 10.0  # Remove after this time
    
    def update(self, dt: float) -> None:
        """Decay danger zone over time"""
        self.lifetime += dt
    
    def is_expired(self) -> bool:
        """Check if zone should be removed"""
        return self.lifetime > self.max_lifetime
    
    def get_danger_at(self, x: float, y: float) -> float:
        """Get danger level at position (0.0-1.0)"""
        dist = math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)
        
        if dist > self.radius:
            return 0.0
        
        # Danger decreases from center
        falloff = 1.0 - (dist / self.radius)
        return falloff * self.severity


class DangerMap:
    """
    Real-time danger assessment
    
    Tracks:
    - Enemy positions & threat levels
    - Hazard zones (toxic, lava, etc.)
    - Boss locations
    - Projectile concentrations
    """
    
    def __init__(self, tile_size: float = 64.0, cell_size: float = 128.0):
        self.tile_size = tile_size
        self.cell_size = cell_size  # Grid cell for spatial hashing
        
        # Danger zones
        self.danger_zones: List[DangerZone] = []
        self.zone_cells: Dict[Tuple[int, int], List[DangerZone]] = {}
        
        # Global danger state
        self.global_danger_level: float = 0.0  # Average of all zones
        self.max_danger: Tuple[float, float, float] = (0, 0, 0)  # x, y, danger
        
        # Performance
        self.update_counter: int = 0
        self.danger_cache: Dict[Tuple[int, int], float] = {}
    
    def add_enemy_threat(self, x: float, y: float, 
                        enemy_health: float, max_health: float,
                        radius: float = 300.0) -> None:
        """Add danger zone from enemy"""
        severity = (enemy_health / max_health) * 0.8 + 0.2  # Scale 0.2-1.0
        zone = DangerZone(x, y, radius, "enemy", severity)
        self._add_zone(zone)
    
    def add_boss_threat(self, x: float, y: float,
                       boss_health: float, max_health: float,
                       radius: float = 400.0) -> None:
        """Add danger zone from boss (higher severity)"""
        severity = (boss_health / max_health) * 0.9 + 0.4  # Scale 0.4-1.3, clamped to 1.0
        zone = DangerZone(x, y, radius, "boss", min(severity, 1.0))
        self._add_zone(zone)
    
    def add_hazard_zone(self, x: float, y: float,
                       hazard_type: str, radius: float = 200.0,
                       severity: float = 0.7) -> None:
        """Add danger from environmental hazard"""
        zone = DangerZone(x, y, radius, f"hazard_{hazard_type}", severity)
        self._add_zone(zone)
    
    def add_projectile_cluster(self, x: float, y: float,
                             projectile_count: int,
                             radius: float = 150.0) -> None:
        """Add danger from projectile concentration"""
        severity = min(projectile_count / 10.0, 1.0)  # Scale: 0.1 per projectile
        zone = DangerZone(x, y, radius, "projectile", severity)
        self._add_zone(zone)
    
    def add_crowd_threat(self, enemies: List, radius: float = 250.0) -> None:
        """Add danger from enemy group (crowd danger)"""
        if not enemies:
            return
        
        # Calculate centroid of enemy group
        avg_x = sum(e.x for e in enemies) / len(enemies)
        avg_y = sum(e.y for e in enemies) / len(enemies)
        
        # Danger increases with group size
        severity = min(len(enemies) / 5.0, 1.0)  # Scale: 0.2 per enemy
        zone = DangerZone(avg_x, avg_y, radius, "crowd", severity)
        self._add_zone(zone)
    
    def _add_zone(self, zone: DangerZone) -> None:
        """Add zone to map with spatial hashing"""
        self.danger_zones.append(zone)
        
        # Hash to cells
        cell_x = int(zone.x / self.cell_size)
        cell_y = int(zone.y / self.cell_size)
        key = (cell_x, cell_y)
        
        if key not in self.zone_cells:
            self.zone_cells[key] = []
        self.zone_cells[key].append(zone)
    
    def get_danger_at(self, x: float, y: float) -> float:
        """Get danger level at position (0.0-1.0)"""
        # Check cache
        cell_x = int(x / self.cell_size)
        cell_y = int(y / self.cell_size)
        cache_key = (cell_x, cell_y)
        
        if cache_key in self.danger_cache and self.update_counter % 10 == 0:
            return self.danger_cache[cache_key]
        
        # Calculate from nearby zones only
        danger = 0.0
        
        # Check current cell and neighbors
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                neighbor_key = (cell_x + dx, cell_y + dy)
                if neighbor_key in self.zone_cells:
                    for zone in self.zone_cells[neighbor_key]:
                        zone_danger = zone.get_danger_at(x, y)
                        danger = max(danger, zone_danger)
        
        # Cache
        self.danger_cache[cache_key] = danger
        return danger
    
    def get_danger_gradient(self, x: float, y: float, 
                           sample_distance: float = 50.0) -> Tuple[float, float]:
        """
        Get danger gradient (direction of increasing danger)
        Returns (dx, dy) normalized vector pointing toward danger
        """
        # Sample danger in 4 directions
        north = self.get_danger_at(x, y - sample_distance)
        south = self.get_danger_at(x, y + sample_distance)
        east = self.get_danger_at(x + sample_distance, y)
        west = self.get_danger_at(x - sample_distance, y)
        
        # Gradient
        dy = south - north
        dx = east - west
        
        # Normalize
        magnitude = math.sqrt(dx * dx + dy * dy)
        if magnitude > 0:
            dx /= magnitude
            dy /= magnitude
        
        return dx, dy
    
    def get_escape_direction(self, x: float, y: float) -> Tuple[float, float]:
        """Get direction away from danger"""
        gradient_x, gradient_y = self.get_danger_gradient(x, y)
        # Escape is opposite of gradient
        magnitude = math.sqrt(gradient_x * gradient_x + gradient_y * gradient_y)
        if magnitude > 0:
            return -gradient_x / magnitude, -gradient_y / magnitude
        return 0, 0
    
    def get_safe_zones(self, player_x: float, player_y: float,
                      search_radius: float = 500.0,
                      safe_threshold: float = 0.2) -> List[Tuple[float, float]]:
        """Find safe zones (low danger areas)"""
        safe_zones = []
        
        # Sample grid
        sample_count = int(search_radius / self.cell_size) * 2
        for i in range(-sample_count, sample_count + 1):
            for j in range(-sample_count, sample_count + 1):
                sx = player_x + i * self.cell_size
                sy = player_y + j * self.cell_size
                
                danger = self.get_danger_at(sx, sy)
                if danger < safe_threshold:
                    safe_zones.append((sx, sy))
        
        # Sort by distance
        safe_zones.sort(
            key=lambda pos: (pos[0] - player_x) ** 2 + (pos[1] - player_y) ** 2
        )
        
        return safe_zones[:10]  # Return top 10
    
    def update(self, dt: float) -> None:
        """Update danger map"""
        self.update_counter += 1
        
        # Update zones
        expired = []
        for zone in self.danger_zones:
            zone.update(dt)
            if zone.is_expired():
                expired.append(zone)
        
        # Remove expired zones
        for zone in expired:
            self.danger_zones.remove(zone)
            # Clean up cells
            cell_x = int(zone.x / self.cell_size)
            cell_y = int(zone.y / self.cell_size)
            key = (cell_x, cell_y)
            if key in self.zone_cells and zone in self.zone_cells[key]:
                self.zone_cells[key].remove(zone)
        
        # Clear cache periodically
        if self.update_counter % 30 == 0:
            self.danger_cache.clear()
        
        # Update global danger
        if self.danger_zones:
            self.global_danger_level = sum(z.severity for z in self.danger_zones) / len(self.danger_zones)
        else:
            self.global_danger_level = 0.0
    
    def get_threat_assessment(self) -> Dict[str, any]:
        """Get overall threat assessment"""
        return {
            "global_danger": self.global_danger_level,
            "active_zones": len(self.danger_zones),
            "zone_types": self._count_zone_types(),
        }
    
    def _count_zone_types(self) -> Dict[str, int]:
        """Count zones by type"""
        counts = {}
        for zone in self.danger_zones:
            counts[zone.danger_type] = counts.get(zone.danger_type, 0) + 1
        return counts
    
    def clear(self) -> None:
        """Clear all danger zones"""
        self.danger_zones.clear()
        self.zone_cells.clear()
        self.danger_cache.clear()
        self.global_danger_level = 0.0
    
    def get_debug_info(self) -> Dict[str, any]:
        """Get debug information"""
        return {
            "active_zones": len(self.danger_zones),
            "zone_types": self._count_zone_types(),
            "global_danger": self.global_danger_level,
            "cache_size": len(self.danger_cache),
        }
