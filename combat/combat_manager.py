from typing import List


class CombatManager:
    """
    Centralized combat resolution.
    Checks attacker.attack_box vs defender.hurtbox.
    Uses AttackBox.hit_set to ensure one hit per activation (no multi-hit spam).
    """

    def __init__(self, screen_effects=None):
        self.screen_effects = screen_effects

    def check_combat_collisions(self, attackers: list, defenders: list) -> None:
        """
        For every active attacker, check if its attack_box overlaps any defender's hurtbox.
        Damage is applied at most once per (attacker, defender) pair per attack activation.
        """
        for attacker in attackers:
            atk_box = getattr(attacker, 'attack_box', None)
            if atk_box is None or not atk_box.active:
                continue

            for defender in defenders:
                if attacker is defender:
                    continue

                hurtbox = getattr(defender, 'hurtbox', None)
                if hurtbox is None:
                    continue

                # Skip if already hit this defender this swing
                if hasattr(atk_box, 'already_hit') and atk_box.already_hit(defender):
                    continue

                # Skip if defender is currently invincible
                if hurtbox.is_invincible():
                    continue

                if atk_box.rect.colliderect(hurtbox.rect):
                    self._apply_damage(attacker, defender)
                    # Mark defender as hit for this swing (prevents multi-hit)
                    if hasattr(atk_box, 'mark_hit'):
                        atk_box.mark_hit(defender)

    def _apply_damage(self, attacker, defender) -> None:
        """Apply damage from attacker to defender using the entity's take_damage() method."""
        if not hasattr(defender, 'take_damage'):
            return

        atk_box = attacker.attack_box
        damage = atk_box.damage

        # Build a damage source for context
        defender.take_damage(damage, attacker)
        
        # Set hit flag for projectiles
        if hasattr(attacker, 'hit_something'):
            attacker.hit_something = True

        # Combat polish feedback (visuals, freeze frames)
        try:
            is_critical = getattr(atk_box, 'is_critical', False)
            if hasattr(self, 'polish') and self.polish:
                self.polish.on_hit(getattr(attacker, 'x', 0), getattr(attacker, 'y', 0),
                                   getattr(defender, 'x', 0), getattr(defender, 'y', 0),
                                   is_critical, damage)
        except Exception:
            pass

        # Play hit SFX
        try:
            if hasattr(self, 'combat_sounds') and self.combat_sounds:
                hit_type = 'critical' if getattr(atk_box, 'is_critical', False) else 'normal'
                self.combat_sounds.play_hit_sound(hit_type)
        except Exception:
            pass

        # Trigger camera shake via attacker if it has a camera reference (player only)
        cam = getattr(attacker, '_camera_ref', None)
        if cam and hasattr(cam, 'add_shake'):
            cam.add_shake(intensity=4, duration=0.1)

        # If defender died, play death sound
        try:
            if hasattr(defender, 'is_dead') and defender.is_dead:
                if hasattr(self, 'combat_sounds') and self.combat_sounds:
                    # Distinguish boss vs enemy vs player
                    etype = 'enemy'
                    if getattr(defender, '__class__', None):
                        name = getattr(defender.__class__, '__name__', '').lower()
                        if 'boss' in name:
                            etype = 'boss'
                        if 'player' in name:
                            etype = 'player'
                    self.combat_sounds.play_death_sound(etype)
        except Exception:
            pass
