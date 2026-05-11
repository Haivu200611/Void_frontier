"""
Game balance adjustments and difficulty settings.
"""

from typing import Dict


class DifficultySettings:
    """Difficulty level configurations."""
    
    EASY = {
        'enemy_hp_multiplier': 0.7,
        'enemy_damage_multiplier': 0.6,
        'enemy_speed_multiplier': 0.8,
        'boss_hp_multiplier': 0.6,
        'boss_damage_multiplier': 0.5,
        'loot_drop_chance_multiplier': 1.5,
        'xp_multiplier': 1.2,
    }
    
    NORMAL = {
        'enemy_hp_multiplier': 1.0,
        'enemy_damage_multiplier': 1.0,
        'enemy_speed_multiplier': 1.0,
        'boss_hp_multiplier': 1.0,
        'boss_damage_multiplier': 1.0,
        'loot_drop_chance_multiplier': 1.0,
        'xp_multiplier': 1.0,
    }
    
    HARD = {
        'enemy_hp_multiplier': 1.4,
        'enemy_damage_multiplier': 1.3,
        'enemy_speed_multiplier': 1.2,
        'boss_hp_multiplier': 1.5,
        'boss_damage_multiplier': 1.4,
        'loot_drop_chance_multiplier': 0.8,
        'xp_multiplier': 1.5,
    }
    
    SURVIVAL = {
        'enemy_hp_multiplier': 1.8,
        'enemy_damage_multiplier': 1.6,
        'enemy_speed_multiplier': 1.4,
        'boss_hp_multiplier': 2.0,
        'boss_damage_multiplier': 1.8,
        'loot_drop_chance_multiplier': 0.5,
        'xp_multiplier': 2.0,
    }


class GameBalance:
    """Game balance tuning parameters."""
    
    # Progression pacing
    PROGRESSION_PACING = {
        'initial_ore_spread': 30,  # World units between ore spawns
        'ore_spread_per_biome': 20,
        'mining_time_base': 2.0,  # seconds
        'crafting_speed': 1.5,  # recipes per second
    }
    
    # Combat balance
    COMBAT_BALANCE = {
        'player_base_damage': 20,
        'player_attack_cooldown': 0.35,
        'player_projectile_damage': 15,
        'player_projectile_cooldown': 0.25,
        
        'enemy_base_damage': 10,
        'enemy_base_hp': 30,
        'enemy_attack_cooldown': 1.5,
        
        'boss_base_damage': 25,
        'boss_base_hp': 200,
        'boss_attack_cooldown': 2.0,
    }
    
    # Crafting costs
    CRAFTING_COSTS = {
        'tool_iron_pickaxe': {'scrap_metal': 5, 'stone': 10},
        'medkit_small': {'plant_fiber': 3, 'mineral': 2},
        'oxygen_pack': {'tech_core': 1, 'scrap_metal': 3},
        'food_pack': {'plant_fiber': 5},
    }
    
    # Loot drops
    LOOT_DROPS = {
        'enemy': {
            'scrap_metal': 0.4,
            'plant_fiber': 0.3,
            'health_drop': 0.2,
        },
        'boss': {
            'tech_core': 0.6,
            'artifact': 0.1,
            'health_drop': 0.8,
        },
    }
    
    # Difficulty scaling
    DIFFICULTY_SCALING = {
        'world_1': 1.0,  # toxic_plains
        'world_2': 1.3,  # crystal_desert
        'world_3': 1.6,  # fungal_cave
        'world_4': 2.0,  # void_ruins
    }


def get_difficulty_settings(difficulty: str = "normal") -> Dict:
    """Get difficulty settings."""
    difficulty_map = {
        "easy": DifficultySettings.EASY,
        "normal": DifficultySettings.NORMAL,
        "hard": DifficultySettings.HARD,
        "survival": DifficultySettings.SURVIVAL,
    }
    
    return difficulty_map.get(difficulty.lower(), DifficultySettings.NORMAL)


def apply_difficulty_multiplier(base_value: float, multiplier_key: str, 
                               difficulty: str = "normal") -> float:
    """Apply difficulty multiplier to a value."""
    settings = get_difficulty_settings(difficulty)
    return base_value * settings.get(multiplier_key, 1.0)
