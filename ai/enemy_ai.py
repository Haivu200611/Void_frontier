import math
import random


class EnemyState:
    IDLE   = 0
    PATROL = 1
    CHASE  = 2
    ATTACK = 3
    FLEE   = 4


class EnemyAI:
    """
    Finite-state machine AI for DummyEnemy.
    States: IDLE → CHASE → ATTACK → CHASE (loop)
    Implements attack cooldown to prevent per-frame damage.
    """

    def __init__(self, entity):
        self.entity = entity
        self.state = EnemyState.IDLE
        self.target = None

        # Radii
        self.aggro_radius:   float = 420.0
        self.deaggro_radius: float = 560.0
        self.attack_radius:  float = 55.0   # distance to switch to ATTACK

        # Attack cooldown (seconds between attack activations)
        self.attack_cooldown: float = 1.2
        self.attack_timer:    float = 0.0

        # Patrol wander
        self._patrol_target_x: float = entity.x
        self._patrol_target_y: float = entity.y
        self._patrol_timer: float = 0.0

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float, players: list) -> None:
        if not players:
            return

        player = players[0]
        dist = math.hypot(self.entity.x - player.x, self.entity.y - player.y)

        # Tick attack cooldown
        if self.attack_timer > 0:
            self.attack_timer -= dt

        # --- FSM transitions ---
        if self.state == EnemyState.IDLE:
            self._idle(dt, player, dist)

        elif self.state == EnemyState.PATROL:
            self._patrol(dt, player, dist)

        elif self.state == EnemyState.CHASE:
            self._chase(dt, player, dist)

        elif self.state == EnemyState.ATTACK:
            self._attack(dt, player, dist)

    # ------------------------------------------------------------------
    # State behaviours
    # ------------------------------------------------------------------

    def _idle(self, dt: float, player, dist: float) -> None:
        self.entity.velocity_x = 0.0
        self.entity.velocity_y = 0.0

        if dist < self.aggro_radius:
            self.state = EnemyState.CHASE
        else:
            # Occasionally switch to patrol
            self._patrol_timer -= dt
            if self._patrol_timer <= 0:
                self._patrol_timer = random.uniform(3.0, 7.0)
                angle = random.uniform(0, math.tau)
                wander = random.uniform(60, 200)
                self._patrol_target_x = self.entity.x + math.cos(angle) * wander
                self._patrol_target_y = self.entity.y + math.sin(angle) * wander
                self.state = EnemyState.PATROL

    def _patrol(self, dt: float, player, dist: float) -> None:
        if dist < self.aggro_radius:
            self.state = EnemyState.CHASE
            return

        dx = self._patrol_target_x - self.entity.x
        dy = self._patrol_target_y - self.entity.y
        d  = math.hypot(dx, dy)

        if d < 10:
            self.state = EnemyState.IDLE
            self.entity.velocity_x = 0.0
            self.entity.velocity_y = 0.0
        else:
            spd = self.entity.speed * 0.3
            self.entity.velocity_x = (dx / d) * spd
            self.entity.velocity_y = (dy / d) * spd

    def _chase(self, dt: float, player, dist: float) -> None:
        if dist > self.deaggro_radius:
            self.state = EnemyState.IDLE
            self.entity.velocity_x = 0.0
            self.entity.velocity_y = 0.0
            return

        if dist <= self.attack_radius:
            self.state = EnemyState.ATTACK
            return

        dx = player.x - self.entity.x
        dy = player.y - self.entity.y
        spd = self.entity.speed * 0.55
        self.entity.velocity_x = (dx / dist) * spd
        self.entity.velocity_y = (dy / dist) * spd

    def _attack(self, dt: float, player, dist: float) -> None:
        # Stop moving while attacking
        self.entity.velocity_x = 0.0
        self.entity.velocity_y = 0.0

        if dist > self.attack_radius * 1.5:
            # Player escaped — re-enter chase
            self.state = EnemyState.CHASE
            if self.entity.attack_box:
                self.entity.attack_box.hit_set.clear()
            return

        # Activate attack box on cooldown (not every frame!)
        if self.attack_timer <= 0:
            self.attack_timer = self.attack_cooldown
            if self.entity.attack_box:
                # Clear hit set so the next attack window can hit fresh targets
                self.entity.attack_box.hit_set.clear()
