import pygame
from enum import IntFlag


class CollisionLayer(IntFlag):
    """Bit-flag collision layers for filtering."""
    PLAYER      = 1
    ENEMY       = 2
    ENVIRONMENT = 4
    PROJECTILE  = 8
    ITEM        = 16
    ALL         = PLAYER | ENEMY | ENVIRONMENT | PROJECTILE | ITEM


class CollisionSystem:
    """
    Static-method collision system.
    Handles:
      - Entity vs static obstacle (AABB resolution, axis-separated, no jitter)
      - Entity vs entity separation (swarm/clumping prevention)
    All resolution happens on entity.x / entity.y then syncs hitbox and rect.
    """

    # ------------------------------------------------------------------
    # Core AABB push-out
    # ------------------------------------------------------------------

    @staticmethod
    def resolve_aabb(entity, obstacle_rect: pygame.Rect) -> bool:
        """
        Push entity out of a static obstacle rect.
        Resolves along the axis of minimal overlap to prevent jitter.
        Returns True if a collision was resolved.
        """
        if not hasattr(entity, 'hitbox'):
            return False
        if not entity.hitbox.rect.colliderect(obstacle_rect):
            return False

        ex = entity.hitbox.rect.centerx
        ey = entity.hitbox.rect.centery
        ox = obstacle_rect.centerx
        oy = obstacle_rect.centery

        dx = ex - ox
        dy = ey - oy

        # Half-sums
        hw = (entity.hitbox.rect.width  + obstacle_rect.width)  * 0.5
        hh = (entity.hitbox.rect.height + obstacle_rect.height) * 0.5

        overlap_x = hw - abs(dx)
        overlap_y = hh - abs(dy)

        if overlap_x <= 0 or overlap_y <= 0:
            return False  # No real overlap

        # Resolve along axis with smaller penetration (SAT minimum push)
        if overlap_x < overlap_y:
            push = overlap_x if dx >= 0 else -overlap_x
            entity.x += push
            # Zero only the relevant velocity component to stop tunnelling
            if hasattr(entity, 'velocity_x'):
                entity.velocity_x = 0.0
        else:
            push = overlap_y if dy >= 0 else -overlap_y
            entity.y += push
            if hasattr(entity, 'velocity_y'):
                entity.velocity_y = 0.0

        # Sync rect and hitbox after resolution
        CollisionSystem._sync_entity(entity)
        return True

    # ------------------------------------------------------------------
    # Entity separation (soft push-apart for enemies)
    # ------------------------------------------------------------------

    @staticmethod
    def separate_entities(entity_a, entity_b,
                          weight_a: float = 0.5, weight_b: float = 0.5) -> bool:
        """
        Prevent two dynamic entities from overlapping.
        Weights control how much each entity moves (default 50/50).
        Returns True if separation was applied.
        """
        if not (hasattr(entity_a, 'hitbox') and hasattr(entity_b, 'hitbox')):
            return False
        if not entity_a.hitbox.rect.colliderect(entity_b.hitbox.rect):
            return False

        ax = entity_a.hitbox.rect.centerx
        ay = entity_a.hitbox.rect.centery
        bx = entity_b.hitbox.rect.centerx
        by = entity_b.hitbox.rect.centery

        dx = ax - bx
        dy = ay - by

        # Degenerate case: perfectly stacked
        if dx == 0 and dy == 0:
            dx = 1.0

        hw = (entity_a.hitbox.rect.width  + entity_b.hitbox.rect.width)  * 0.5
        hh = (entity_a.hitbox.rect.height + entity_b.hitbox.rect.height) * 0.5

        overlap_x = hw - abs(dx)
        overlap_y = hh - abs(dy)

        if overlap_x <= 0 or overlap_y <= 0:
            return False

        if overlap_x < overlap_y:
            push = overlap_x if dx >= 0 else -overlap_x
            entity_a.x += push * weight_a
            entity_b.x -= push * weight_b
        else:
            push = overlap_y if dy >= 0 else -overlap_y
            entity_a.y += push * weight_a
            entity_b.y -= push * weight_b

        CollisionSystem._sync_entity(entity_a)
        CollisionSystem._sync_entity(entity_b)
        return True

    # ------------------------------------------------------------------
    # Batch helpers used by PlayState
    # ------------------------------------------------------------------

    @staticmethod
    def handle_static_collisions(entity, obstacles: list) -> None:
        """Resolve entity against all obstacles in list. Iterates twice to settle."""
        for obs in obstacles:
            if hasattr(obs, 'rect'):
                CollisionSystem.resolve_aabb(entity, obs.rect)
        # Second pass to catch corner cases / diagonal tunnelling
        for obs in obstacles:
            if hasattr(obs, 'rect'):
                CollisionSystem.resolve_aabb(entity, obs.rect)

    @staticmethod
    def handle_entity_separations(entities: list) -> None:
        """
        O(N²) pairwise separation. Acceptable for < ~50 entities.
        For larger groups, replace with spatial hashing.
        """
        n = len(entities)
        for i in range(n):
            for j in range(i + 1, n):
                CollisionSystem.separate_entities(entities[i], entities[j])

    @staticmethod
    def projectile_hits_obstacle(proj, obstacles: list) -> bool:
        """
        Check if a projectile overlaps any obstacle.
        Returns True and deactivates the projectile on first hit.
        """
        for obs in obstacles:
            if hasattr(obs, 'rect') and proj.attack_box.rect.colliderect(obs.rect):
                proj.deactivate()
                return True
        return False

    # ------------------------------------------------------------------
    # Internal sync utility
    # ------------------------------------------------------------------

    @staticmethod
    def _sync_entity(entity) -> None:
        """Keep entity.rect and entity.hitbox in sync after position change."""
        entity.rect.center = (int(entity.x), int(entity.y))
        if hasattr(entity, 'hitbox') and entity.hitbox:
            entity.hitbox.update(entity.x, entity.y)
        if hasattr(entity, 'hurtbox') and entity.hurtbox:
            # Hurtbox syncs on its own update() but we force it here too
            entity.hurtbox.rect.center = entity.hitbox.rect.center
