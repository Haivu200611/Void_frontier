from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional


class DamageType(Enum):
    """Categories of damage — used for resistances, VFX, and sound later."""
    PHYSICAL  = auto()   # Melee, blunt
    ENERGY    = auto()   # Laser, plasma
    EXPLOSIVE = auto()   # Grenade, rocket
    TRUE      = auto()   # Bypasses all resistances
    POISON    = auto()   # Damage over time
    VOID      = auto()   # Late-game exotic damage


@dataclass
class DamageSource:
    """
    Encapsulates all metadata about a damage event.
    Passed to entity.take_damage() so receivers can react (VFX, sound, etc.).
    """
    amount:        float
    damage_type:   DamageType        = DamageType.PHYSICAL
    knockback:     float             = 0.0
    source_entity: Optional[object]  = None   # The entity that caused the damage

    # ------------------------------------------------------------------ 
    # Convenience constructors
    # ------------------------------------------------------------------
    @classmethod
    def melee(cls, amount: float, knockback: float = 5.0, source=None) -> "DamageSource":
        return cls(amount, DamageType.PHYSICAL, knockback, source)

    @classmethod
    def projectile(cls, amount: float, knockback: float = 2.0, source=None) -> "DamageSource":
        return cls(amount, DamageType.ENERGY, knockback, source)

    @classmethod
    def contact(cls, amount: float, knockback: float = 3.0, source=None) -> "DamageSource":
        """Enemy body-contact damage."""
        return cls(amount, DamageType.PHYSICAL, knockback, source)
