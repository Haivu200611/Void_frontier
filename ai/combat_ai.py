"""
Auto Combat System
Intelligent combat decision making and execution
"""
from typing import Optional, List, Tuple
import math


class CombatAI:
    """
    Handles combat decisions for auto mode
    - Target selection
    - Dodge tactics
    - Chase & attack
    - Retreat logic
    """
    
    def __init__(self, player, blackboard, danger_map):
        self.player = player
        self.blackboard = blackboard
        self.danger_map = danger_map
        
        self.current_target: Optional[any] = None
        self.target_acquired_time: float = 0.0
        self.last_dodge_time: float = 0.0
        self.dodge_cooldown: float = 0.5
        
        # Combat stats
        self.aggressiveness: float = 0.7  # 0.0 (passive) to 1.0 (aggressive)
        self.preferred_range: float = 250.0  # Ranged attack distance
    
    def select_target(self, enemies: List) -> Optional[any]:
        """
        Intelligent target selection
        Prioritize based on: threat, health, distance
        """
        if not enemies:
            return None
        
        # Score each enemy
        best_target = None
        best_score = -1
        
        for enemy in enemies:
            if enemy.is_dead:
                continue
            
            dist = self._distance(
                (self.player.x, self.player.y),
                (enemy.x, enemy.y)
            )
            
            # Threat score
            threat = (enemy.health / max(1.0, enemy.max_health))
            
            # Distance score (closer = better if not too close)
            dist_score = 1.0 / (1.0 + dist / 100.0)
            
            # Combine scores
            score = (threat * 0.3 + dist_score * 0.7)
            
            # Prioritize if already targeting (hysteresis)
            if enemy == self.current_target:
                score *= 1.2
            
            if score > best_score:
                best_score = score
                best_target = enemy
        
        return best_target
    
    def get_combat_distance(self, target) -> float:
        """Get distance to target"""
        return self._distance(
            (self.player.x, self.player.y),
            (target.x, target.y)
        )
    
    def should_attack(self, target) -> bool:
        """Check if should attack"""
        if not target or target.is_dead:
            return False
        
        dist = self.get_combat_distance(target)
        
        # In range
        if dist <= self.preferred_range + 50:
            return True
        
        return False
    
    def should_dodge(self, enemies: List) -> Tuple[bool, Tuple[float, float]]:
        """
        Check if should dodge and return dodge direction
        """
        if len(enemies) == 0:
            return False, (0, 0)
        
        # Check threat
        threat = self.danger_map.global_danger_level
        hp_ratio = self.player.health / max(1.0, self.player.max_health)
        
        # Don't dodge if low threat or we're aggressive
        if threat < 0.4 or self.aggressiveness > 0.8:
            return False, (0, 0)
        
        # Dodge if HP is low
        if hp_ratio < 0.4:
            dodge_dir = self.danger_map.get_escape_direction(
                self.player.x, self.player.y
            )
            return True, dodge_dir
        
        return False, (0, 0)
    
    def get_chase_direction(self, target) -> Tuple[float, float]:
        """Get direction to chase target"""
        dx = target.x - self.player.x
        dy = target.y - self.player.y
        dist = math.sqrt(dx * dx + dy * dy)
        
        if dist > 0:
            return dx / dist, dy / dist
        return 0, 0
    
    def get_retreat_direction(self, enemies: List) -> Tuple[float, float]:
        """Get direction to retreat from enemies"""
        if not enemies:
            return 0, 0
        
        # Retreat away from nearest enemy
        nearest = min(enemies, key=lambda e: self._distance(
            (self.player.x, self.player.y),
            (e.x, e.y)
        ))
        
        dx = self.player.x - nearest.x
        dy = self.player.y - nearest.y
        dist = math.sqrt(dx * dx + dy * dy)
        
        if dist > 0:
            return dx / dist, dy / dist
        return 0, 0
    
    def update_aggressiveness(self, hp_ratio: float, threat_level: float) -> None:
        """Update aggressiveness based on situation"""
        # Low health = less aggressive
        # High threat = less aggressive
        # Good health + low threat = more aggressive
        
        base_aggressiveness = 0.7
        hp_factor = hp_ratio  # 1.0 if full, 0.0 if dead
        threat_factor = 1.0 - threat_level  # 1.0 if safe, 0.0 if critical
        
        self.aggressiveness = (base_aggressiveness * hp_factor * threat_factor)
        self.aggressiveness = max(0.1, min(1.0, self.aggressiveness))  # Clamp
    
    def perform_attack(self, target) -> None:
        """Perform attack action (Melee)"""
        if not self.player.is_attacking and self.player.attack_timer <= 0:
            self.player.is_attacking = True
            self.player.attack_timer = self.player.attack_cooldown
            self.player.attack_box.activate()
            
            # Point attack at target
            dx = target.x - self.player.x
            dy = target.y - self.player.y
            dist = math.sqrt(dx * dx + dy * dy)
            
            if dist > 0:
                self.player.attack_box.offset_x = (dx / dist) * (self.player.width * 0.5 + 50)
                self.player.attack_box.offset_y = (dy / dist) * (self.player.width * 0.5 + 50)

    def perform_shoot(self, target, projectile_pool) -> None:
        """Perform shooting action (Ranged)"""
        if not projectile_pool:
            return
            
        if self.player.shoot_timer <= 0:
            # We use a dummy camera object to satisfy the _shoot signature if needed,
            # or we just reimplement the logic here for the AI.
            # Looking at player.py, _shoot takes camera and projectile_pool.
            # But the AI doesn't have a camera. We can simulate the dx, dy directly.
            
            # Default kinetic stats
            dmg = 15
            spd = 640
            cool = 0.25
            life = 2.0
            clr = (0, 220, 255)
            
            # Check equipped weapon
            if hasattr(self.player, 'inventory') and self.player.inventory:
                weapon_stack = self.player.inventory.equipment.get("weapon")
                if weapon_stack:
                    from systems.items import ItemDatabase
                    item = ItemDatabase.get_item(weapon_stack.item_id)
                    if item and item.weapon_stats:
                        stats = item.weapon_stats
                        dmg = stats.get("damage", dmg)
                        spd = stats.get("speed", spd)
                        cool = stats.get("cooldown", cool)
                        life = stats.get("lifetime", life)
                        clr = tuple(stats.get("color", clr))

            self.player.shoot_timer = cool
            dx = target.x - self.player.x
            dy = target.y - self.player.y
            
            projectile_pool.spawn(
                self.player.x,
                self.player.y,
                dx,
                dy,
                speed=spd,
                lifetime=life,
                damage=dmg,
                color=clr,
                radius=4,
                owner_layer="player",
            )
    
    def execute_combat(self, enemies: List, projectile_pool=None) -> Tuple[float, float]:
        """
        Execute combat logic using Heuristics for target selection 
        and A* (via navigation) for positioning.
        Returns (velocity_x, velocity_y)
        """
        # Update aggressiveness using Heuristic-based logic
        hp_ratio = self.player.health / max(1.0, self.player.max_health)
        self.update_aggressiveness(hp_ratio, self.danger_map.global_danger_level)
        
        # Select target using Heuristic scoring (threat, health, distance)
        target = self.select_target(enemies)
        if not target:
            return 0, 0
        
        self.current_target = target
        
        # Boss detection
        is_boss = hasattr(target, "phase") or "Boss" in str(type(target))
        
        # Dynamic range based on target type
        # Bosses: Stay further away (250-350 range)
        # Normal: Close in (preferred_range)
        target_range = 300.0 if is_boss else self.preferred_range
        
        # Check dodge using Danger Map Heuristics
        should_dodge, dodge_dir = self.should_dodge(enemies)
        if is_boss:
            # Bosses are more dangerous, dodge more aggressively
            if self.danger_map.global_danger_level > 0.3:
                should_dodge = True
                dodge_dir = self.danger_map.get_escape_direction(self.player.x, self.player.y)

        if should_dodge:
            velocity_x = dodge_dir[0] * self.player.base_speed * 1.2
            velocity_y = dodge_dir[1] * self.player.base_speed * 1.2
            return velocity_x, velocity_y
        
        # Check retreat using Heuristic (HP < 30% and High Threat)
        if self.danger_map.global_danger_level > 0.8 and hp_ratio < 0.3:
            retreat_dir = self.get_retreat_direction(enemies)
            velocity_x = retreat_dir[0] * self.player.base_speed
            velocity_y = retreat_dir[1] * self.player.base_speed
            return velocity_x, velocity_y
        
        # Position and Attack
        dist = self.get_combat_distance(target)
        
        # AI now defaults to using its built-in kinetic blaster if no weapon is equipped
        has_gun = True
            
        if dist > target_range:
            # Chase
            chase_dir = self.get_chase_direction(target)
            velocity_x = chase_dir[0] * self.player.base_speed
            velocity_y = chase_dir[1] * self.player.base_speed
            
            # Shoot while chasing if in range
            if has_gun and dist < 600:
                self.perform_shoot(target, projectile_pool)
        else:
            # In range
            if is_boss:
                # Against boss, don't just stand there. Circle them.
                # Perpendicular direction
                dx = target.x - self.player.x
                dy = target.y - self.player.y
                # Normalize and rotate 90 deg
                mag = math.sqrt(dx*dx + dy*dy)
                if mag > 0:
                    vx, vy = -dy/mag, dx/mag
                    velocity_x = vx * self.player.base_speed * 0.8
                    velocity_y = vy * self.player.base_speed * 0.8
                else:
                    velocity_x, velocity_y = 0, 0
            else:
                # Normal enemy: Keep distance and shoot
                dx = target.x - self.player.x
                dy = target.y - self.player.y
                mag = math.sqrt(dx*dx + dy*dy)
                
                if mag < target_range * 0.7:
                    # Too close, back away
                    velocity_x = -(dx / mag) * self.player.base_speed * 0.6
                    velocity_y = -(dy / mag) * self.player.base_speed * 0.6
                else:
                    # Good range, stop and fire
                    velocity_x = 0
                    velocity_y = 0
                
                # We don't call perform_attack(target) anymore as primary is shooting
            
            # Always try to shoot if in range
            if has_gun and dist < 600:
                self.perform_shoot(target, projectile_pool)
        
        return velocity_x, velocity_y
    
    def get_debug_info(self) -> dict:
        """Get debug info"""
        return {
            "current_target": str(self.current_target) if self.current_target else "None",
            "aggressiveness": f"{self.aggressiveness:.2f}",
        }
    
    @staticmethod
    def _distance(pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
        """Calculate distance"""
        dx = pos2[0] - pos1[0]
        dy = pos2[1] - pos1[1]
        return math.sqrt(dx * dx + dy * dy)
