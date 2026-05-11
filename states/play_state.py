from __future__ import annotations

import random

import pygame

from core.state_machine import State
from settings import *

from entities.player import Player
from entities.npc import NPC
from entities.boss import Boss
from entities.item_drop import HealthDrop, OxygenDrop, FoodDrop
from entities.projectiles.projectile import ProjectilePool

from combat.combat_manager import CombatManager
from combat.collision import CollisionSystem
from combat.status_effects import StatusEffectManager
from combat.combat_polish import CombatPolishSystem, RecoilEffect

from world.world_manager import WorldManager
from world.hazards import HazardManager
from world.portal import Portal, PortalManager, PortalRequirement

from ai.auto_player import AutoPlayerController
from ai.ai_controller import AIController
from ai.pathfinding import Pathfinding

from systems.inventory import Inventory
from systems.items import ItemDatabase
from systems.crafting import CraftingManager
from systems.mining_system import MiningSystem
from systems.save_manager import SaveManager
from systems.spawn_manager import SpawnManager
from systems.progression_manager import ProgressionManager
from systems.trading_system import TradingSystem
from systems.objective_system import ObjectiveSystem
from systems.world_events import WorldEventManager

from combat.boss_manager import BossManager

from core.camera import Camera
from core.screen_effects import ScreenEffects
from particles.particle_system import ParticleSystem
from audio.audio_manager import get_audio_manager, CombatSoundManager
from rendering.environmental_effects import EnvironmentalImmersion
from tools.profiler import get_profiler
from ui.hud import HUD
from ui.boss_healthbar import BossHealthBar
from tools.playtest_tools import get_playtest_console
from combat.enemy_polish import EnemyTelegraph, EnemyHealthBar


_GRID_LINE_CLR = (35, 35, 42)

WORLD_ORDER = ["toxic_plains", "crystal_desert", "fungal_cave", "void_ruins"]
WORLD_BOSS_FLAGS = {
    "toxic_plains": "boss_toxic_plains_defeated",
    "crystal_desert": "boss_crystal_desert_defeated",
    "fungal_cave": "boss_fungal_cave_defeated",
    "void_ruins": "boss_void_ruins_defeated",
}


class PlayState(State):
    def enter(self, **kwargs) -> None:
        ItemDatabase.load("data/items.json")

        self.world_manager = WorldManager(seed="FALLEN_PLANET_SEED", world_id="toxic_plains")
        self.player = Player(1000, 1000)

        self.camera = Camera(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.camera.offset.x = self.player.x - WINDOW_WIDTH * 0.5
        self.camera.offset.y = self.player.y - WINDOW_HEIGHT * 0.5

        self.combat_manager = CombatManager()
        self.spawn_manager = SpawnManager()
        self.projectile_pool = ProjectilePool(max_projectiles=220)
        self.inventory = Inventory(grid_cols=8, grid_rows=4, hotbar_size=9)
        self.crafting = CraftingManager("data/crafting_recipes.json")
        self.mining_system = MiningSystem()
        self.save_manager = SaveManager()
        self.status_effects = StatusEffectManager()
        
        # Initialize visual and audio systems
        self.particle_system = ParticleSystem(max_particles=1000)
        self.screen_effects = ScreenEffects()
        self.audio_manager = get_audio_manager()
        # Combat polish & audio
        self.combat_polish = CombatPolishSystem()
        self.recoil = RecoilEffect()
        self.combat_sounds = CombatSoundManager(self.audio_manager)
        self.environmental_immersion = EnvironmentalImmersion(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.hud = HUD()
        self.boss_healthbar = BossHealthBar()
        self.console = get_playtest_console()
        self.enemy_health_bar = EnemyHealthBar()
        self.telegraphs = []
        self.profiler = get_profiler()
        
        # Pass screen effects and polish/audio to combat manager for impact feedback
        self.combat_manager.screen_effects = self.screen_effects
        self.combat_manager.polish = self.combat_polish
        self.combat_manager.audio_manager = self.audio_manager
        self.combat_manager.combat_sounds = self.combat_sounds

        self.player.inventory = self.inventory

        self.hazard_manager = HazardManager(self.world_manager.seed)
        self.portal_manager = PortalManager()

        self.progression_manager = ProgressionManager()
        self.trading_system = TradingSystem(self.inventory, self.progression_manager)
        self.objective_system = ObjectiveSystem(self.progression_manager)
        self.world_event_manager = WorldEventManager(self.world_manager)
        self.boss_manager = BossManager(self.world_manager, self.player)
        self.endgame_active = False
        self.endgame_timer = 0.0

        self.enemies: list = []
        self.enemy_ais: list = []
        self.npcs: list = []
        self.bosses: list = []
        self.items: list = []

        # Initialize new AI system
        pathfinding = Pathfinding(self.world_manager)
        self.ai_controller = AIController(self.player, self.world_manager, pathfinding)
        
        # Keep old auto_controller for backward compatibility (if needed)
        self.auto_controller = AutoPlayerController(self.player, self.world_manager)

        self.font = pygame.font.SysFont(None, 22)
        self.font_large = pygame.font.SysFont(None, 30)

        self._dead_enemy_drop_set: set = set()
        self.loaded_chunk_keys: list[tuple[int, int]] = []
        self.visible_ores: list = []
        self.visible_hazards: list = []
        self.current_hazard_zone = None

        self.progression_flags = {
            "boss_toxic_plains_defeated": False,
            "boss_crystal_desert_defeated": False,
            "boss_fungal_cave_defeated": False,
            "boss_void_ruins_defeated": False,
            "portal_to_crystal_unlocked": False,
            "portal_to_fungal_unlocked": False,
            "portal_to_void_unlocked": False,
        }
        self.current_boss_spawned = False
        
        # Sync initial progression flags with progression manager
        for boss in self.progression_manager.defeated_bosses:
            if boss == "mecha_beast": self.progression_flags["boss_toxic_plains_defeated"] = True
            elif boss == "crystal_titan": self.progression_flags["boss_crystal_desert_defeated"] = True
            elif boss == "toxic_worm": self.progression_flags["boss_fungal_cave_defeated"] = True
            elif boss == "void_guardian": self.progression_flags["boss_void_ruins_defeated"] = True
        self.world_completion_states = {world_id: False for world_id in WORLD_ORDER}
        self.artifact_tracking = {"alpha": False, "beta": False, "gamma": False}
        self.chapter_1_boss_spawned = False
        self.ship_repair_prompt_active = False
        self.portal_confirm_prompt_active = False
        self.active_portal_target = None
        self.mystery_item_count = 0

        self.portal_save_states: dict[str, list[dict]] = {}
        self.ore_save_states: dict[str, dict[str, dict]] = {}

        self.inventory_open = False
        self.crafting_open = False
        self.selected_recipe_index = 0
        self.recipe_categories = sorted({recipe.category for recipe in self.crafting.recipes})
        self.active_recipe_category = self.recipe_categories[0] if self.recipe_categories else "consumables"

        self.tooltip_text = ""
        self.ui_message = ""
        self.ui_message_timer = 0.0

        self.pending_portal_interact = False
        self.pending_use_hotbar = False
        self.pending_save = False
        self.pending_load = False

        self.consumable_cooldowns: dict[str, float] = {}

        self._seed_starter_inventory()
        self._refresh_world_entities()

    def exit(self) -> None:
        pass

    def handle_events(self, events) -> None:
        for event in events:
            # Console has priority
            if self.console.handle_input(event, play_state=self):
                continue
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKQUOTE:  # ~ key
                    self.console.toggle_open()
                elif event.key == pygame.K_ESCAPE:
                    self.engine.state_machine.change_state("Menu")
                elif event.key == pygame.K_e:
                    self.inventory_open = not self.inventory_open
                elif event.key == pygame.K_c:
                    self.crafting_open = not self.crafting_open
                elif event.key == pygame.K_f:
                    self.pending_portal_interact = True
                elif event.key == pygame.K_r:
                    self.pending_use_hotbar = True
                elif event.key == pygame.K_F5:
                    self.pending_save = True
                elif event.key == pygame.K_F9:
                    self.pending_load = True
                elif pygame.K_1 <= event.key <= pygame.K_9:
                    self.inventory.set_selected_hotbar(event.key - pygame.K_1)
                elif event.key == pygame.K_UP:
                    self.selected_recipe_index = max(0, self.selected_recipe_index - 1)
                elif event.key == pygame.K_DOWN:
                    self.selected_recipe_index = min(len(self._get_active_recipes()) - 1, self.selected_recipe_index + 1)
                elif event.key == pygame.K_RETURN and self.crafting_open:
                    self._craft_selected_recipe()
                elif event.key == pygame.K_g:
                    self.inventory.equip_from_slot(self.inventory.selected_hotbar, "tool")
                elif event.key == pygame.K_q and self.crafting_open:
                    self._cycle_recipe_category(-1)
                elif event.key == pygame.K_w and self.crafting_open:
                    self._cycle_recipe_category(1)
                elif event.key == pygame.K_y:
                    self._handle_confirmation_choice(True)
                elif event.key == pygame.K_n:
                    self._handle_confirmation_choice(False)

            if self.inventory_open:
                self._handle_inventory_mouse(event)

    def update(self, dt: float) -> None:
        # Apply time scaling from slow motion effect and combat hit-freeze
        time_scale = self.screen_effects.get_time_scale() * self.combat_polish.get_time_scale()
        scaled_dt = dt * time_scale
        
        self._tick_ui(scaled_dt)
        self._tick_consumable_cooldowns(scaled_dt)

        self.loaded_chunk_keys = self.world_manager.get_loaded_chunk_keys_near(self.player.x, self.player.y, radius=1)

        for chunk_key in self.loaded_chunk_keys:
            biome = self.world_manager.biome_manager.get_biome_for_chunk(chunk_key[0], chunk_key[1])
            self.hazard_manager.ensure_chunk_zones(chunk_key[0], chunk_key[1], biome.hazard_types)

        self.visible_hazards = self.hazard_manager.get_zones_near(self.loaded_chunk_keys)

        self.spawn_manager.sync_ore_spawns(self.world_manager, self.world_manager.biome_manager, self.loaded_chunk_keys)
        self.visible_ores = self.spawn_manager.get_ores_near(self.loaded_chunk_keys)
        self._apply_saved_ore_states()

        self.mining_system.update(scaled_dt)
        self.spawn_manager.update_ores(scaled_dt, self.loaded_chunk_keys)

        any_auto = self.engine.auto_mine or self.engine.auto_combat_entities or self.engine.auto_combat_boss
        mine_input = False
        if not any_auto:
            keys = pygame.key.get_pressed()
            mouse = pygame.mouse.get_pressed()
            mine_input = mouse[0] and (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])

        if mine_input:
            if self.mining_system.try_mine(self.player, self.visible_ores, self.items, self.camera, mine_input=True):
                self.particle_system.spawn_mining_particles(self.player.x, self.player.y)
                self.screen_effects.trigger_hit(intensity=3, duration=0.05)
                # Mining SFX
                try:
                    self.audio_manager.play_sfx("mine_hit.wav", volume=0.8)
                except Exception:
                    pass

        self.current_hazard_zone = self.hazard_manager.apply_hazards(
            self.player,
            self.status_effects,
            scaled_dt,
            self.loaded_chunk_keys,
        )

        self.status_effects.update(scaled_dt, self.player)
        self.player.status_speed_multiplier = self.status_effects.get_speed_multiplier()

        self.boss_manager.update(scaled_dt)
        self.world_event_manager.update(scaled_dt)

        if not any_auto:
            self.player.update(scaled_dt, self.camera, self.projectile_pool)
        else:
            # Use new AI system with specific flags
            try:
                all_enemies = self.enemies + self.bosses
                self.ai_controller.update(
                    scaled_dt,
                    all_enemies,
                    self.items,
                    self.visible_ores,
                    self.npcs,
                    self.portal_manager.portals,
                    current_hazard_zone=self.current_hazard_zone,
                    current_biome=self.world_manager.current_world_id,
                    auto_mine=self.engine.auto_mine,
                    auto_combat_entities=self.engine.auto_combat_entities,
                    auto_combat_boss=self.engine.auto_combat_boss
                )
                # Update player without handling input (AI sets velocity)
                self.player.handle_combat_timers(scaled_dt)
                self.player.handle_movement(scaled_dt)
                self.player.handle_survival(scaled_dt)
            except Exception as e:
                print(f"AI Controller Error: {e}")
                self._set_ui_message(f"AI Error: {e}", duration=3.0)
                # Disable auto modes to prevent crash loop
                self.engine.auto_mine = False
                self.engine.auto_combat_entities = False
                self.engine.auto_combat_boss = False

        for ai in self.enemy_ais:
            ai.update(scaled_dt, [self.player])

        for enemy in self.enemies:
            enemy.update(scaled_dt)
        for npc in self.npcs:
            npc.update(scaled_dt)
        for boss in self.bosses:
            boss.update(scaled_dt, self.player, self.projectile_pool)

        self.spawn_manager.update(scaled_dt, self.player, self.enemies, self.enemy_ais)
        self.projectile_pool.update(scaled_dt)

        active_obstacles = self.world_manager.get_obstacles_near(self.player.x, self.player.y)
        CollisionSystem.handle_static_collisions(self.player, active_obstacles)
        for enemy in self.enemies:
            CollisionSystem.handle_static_collisions(enemy, active_obstacles)
        for boss in self.bosses:
            CollisionSystem.handle_static_collisions(boss, active_obstacles)

        self.projectile_pool.check_wall_collisions(active_obstacles)
        all_enemies = self.enemies + self.bosses
        CollisionSystem.handle_entity_separations(all_enemies)

        active_projectiles = self.projectile_pool.get_active_projectiles()
        player_projectiles = [p for p in active_projectiles if p.owner_layer == "player"]
        enemy_projectiles = [p for p in active_projectiles if p.owner_layer == "enemy"]

        self.combat_manager.check_combat_collisions([self.player] + player_projectiles, all_enemies)
        self.combat_manager.check_combat_collisions(all_enemies + enemy_projectiles, [self.player])
        
        # Add damage feedback for player hits
        for projectile in player_projectiles:
            if projectile.should_create_particles and projectile.hit_something:
                self.particle_system.spawn_hit_particles(projectile.x, projectile.y)
                # Combat polish and audio for projectile hits
                try:
                    self.combat_polish.on_projectile_hit(projectile.x, projectile.y)
                except Exception:
                    pass
                try:
                    self.combat_sounds.play_hit_sound("normal")
                except Exception:
                    pass

        for enemy in self.enemies:
            if enemy.is_dead and id(enemy) not in self._dead_enemy_drop_set:
                self._dead_enemy_drop_set.add(id(enemy))
                self.particle_system.spawn_blood_particles(enemy.x, enemy.y)
                roll = random.random()
                if roll < 0.20:
                    self.items.append(HealthDrop(enemy.x, enemy.y))
                elif roll < 0.50:
                    self.items.append(OxygenDrop(enemy.x, enemy.y))
                elif roll < 0.80:
                    self.items.append(FoodDrop(enemy.x, enemy.y))
                # Enemy death SFX
                try:
                    self.combat_sounds.play_death_sound("enemy")
                except Exception:
                    pass

        for item in self.items:
            item.update(scaled_dt)
            if item.active and self.player.hitbox.rect.colliderect(item.hitbox.rect):
                if hasattr(item, "apply"):
                    item.apply(self.player)
                    self.particle_system.spawn_energy_particles(self.player.x, self.player.y)
                    self.screen_effects.trigger_hit(intensity=2, duration=0.08)
                    try:
                        self.audio_manager.play_ui_sound("pickup.wav")
                    except Exception:
                        pass

        self._handle_progression_and_rewards()
        self._handle_pending_actions()

        self.enemies = [e for e in self.enemies if not e.is_dead]
        self.bosses = [b for b in self.bosses if not b.is_dead]
        self.enemy_ais = [ai for ai in self.enemy_ais if not ai.entity.is_dead]
        self.items = [i for i in self.items if i.active]
        
        # Update visual and audio systems
        self.particle_system.update(scaled_dt)
        self.screen_effects.update(scaled_dt)
        # Combat polish update (handles hit-freeze timing)
        self.combat_polish.update(scaled_dt)
        self.environmental_immersion.set_biome(self.world_manager.current_world_id)
        self.environmental_immersion.update(scaled_dt, self.camera.offset.x, self.camera.offset.y)
        
        self.hud.update(scaled_dt, self.player)
        if self.bosses:
            boss = self.bosses[0]
            if not self.boss_healthbar.active:
                self.boss_healthbar.show(getattr(boss, 'name', 'BOSS'), boss.max_health)
            self.boss_healthbar.update(scaled_dt, boss.health)
        else:
            self.boss_healthbar.hide()
            self.boss_healthbar.update(scaled_dt, 0)

        self.telegraphs = [t for t in self.telegraphs if t.update(scaled_dt)]

        # Update profiler
        self.profiler.set_counter('entities', len(self.enemies) + len(self.bosses))
        self.profiler.set_counter('projectiles', self.projectile_pool.get_active_count())
        self.profiler.set_counter('particles', self.particle_system.get_active_count())
        self.profiler.set_counter('enemies', len(self.enemies))
        self.profiler.set_counter('bosses', len(self.bosses))

        self.camera.update(self.player, scaled_dt)

        if self.player.is_dead:
            self.engine.state_machine.change_state("Menu")

    def render(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BG)

        offset = self.camera.get_offset()
        shake = self.screen_effects.get_shake_offset()
        ox = int(offset.x + shake[0])
        oy = int(offset.y + shake[1])
        
        # Render environmental effects (parallax and ambient)
        self.environmental_immersion.render(surface)

        self._render_grid(surface, ox, oy)

        self.loaded_chunk_keys = self.world_manager.render(
            surface,
            ox,
            oy,
            self.player.x,
            self.player.y,
            debug_mode=self.engine.debug_mode,
        )

        self.hazard_manager.render(surface, ox, oy, self.visible_hazards, debug=self.engine.debug_mode)

        for ore in self.visible_ores:
            ore.render(surface, ox, oy)

        for item in self.items:
            item.render(surface, ox, oy)

        for npc in self.npcs:
            npc.render(surface, ox, oy)

        for enemy in self.enemies:
            enemy.render(surface, ox, oy)
            # Render health bar if damaged
            if enemy.health < enemy.max_health:
                self.enemy_health_bar.render(surface, enemy.x, enemy.y, enemy.health, 
                                           enemy.max_health, ox, oy)

        for boss in self.bosses:
            boss.render(surface, ox, oy)

        for t in self.telegraphs:
            t.render(surface, ox, oy)
            
        if hasattr(self.boss_manager, 'arena') and self.boss_manager.arena.is_active:
            self.boss_manager.arena.render(surface, ox, oy, self.engine.debug_mode)

        self.portal_manager.render(surface, ox, oy, debug=self.engine.debug_mode)
        self.projectile_pool.render(surface, ox, oy)
        self.player.render(surface, ox, oy)
        
        # Render particles (on top of world but below UI)
        self.particle_system.render(surface, offset.x, offset.y)
        # Combat visual polish (trails, criticals)
        try:
            self.combat_polish.render(surface, offset.x, offset.y)
        except Exception:
            pass

        # Render Progression UI
        self.world_event_manager.render_ui(surface, self.font_large)
        self.objective_system.render_ui(surface, self.font, WINDOW_WIDTH - 300, 20)

        if self.endgame_active:
            # Render endgame timer
            font = pygame.font.SysFont(None, 36)
            text = f"ESCAPE SEQUENCE: {int(60 - self.endgame_timer)}s"
            surf = font.render(text, True, (255, 255, 0))
            surface.blit(surf, (WINDOW_WIDTH // 2 - surf.get_width() // 2, 120))

        if self.engine.debug_mode:
            self._render_debug(surface, ox, oy)
            self.profiler.update(self.engine.clock)
            self.profiler.render_overlay(surface, show_detailed=False)

        # Progression Debug Overlay
        if self.engine.debug_mode:
            self._render_progression_debug(surface)

        self._render_hud(surface)

        if self.inventory_open:
            self._render_inventory(surface)

        if self.crafting_open:
            self._render_crafting(surface)
        
        # Render screen effects (on top of everything)
        self.screen_effects.render(surface)
        
        # Render console (absolute top)
        if self.console.open:
            self.console.render(surface, self.font)

    def _seed_starter_inventory(self) -> None:
        self.inventory.add_item("tool_iron_pickaxe", 1)
        self.inventory.add_item("weapon_basic_gun", 1)
        self.inventory.equip_from_slot(0, "tool")
        self.inventory.equip_from_slot(1, "weapon")

        # Set starting stats based on story: 1/3 Health, 1/4 Oxy, 1/5 Hungry
        self.player.health = self.player.max_health / 3.0
        self.player.oxygen = self.player.max_oxygen / 4.0
        self.player.hunger = self.player.max_hunger / 5.0

    def _refresh_world_entities(self) -> None:
        self.spawn_manager.configure_for_world(self.world_manager.current_world_id)
        self._setup_portals_for_world(self.world_manager.current_world_id)
        self._setup_boss_for_world(self.world_manager.current_world_id)

        self.enemies.clear()
        self.enemy_ais.clear()
        self.items.clear()

        self.auto_controller = AutoPlayerController(self.player, self.world_manager)

    def _setup_boss_for_world(self, world_id: str) -> None:
        self.bosses.clear()
        
        # Chapter 1 boss spawns later based on stats
        if world_id == "toxic_plains":
            return
            
        self._spawn_boss_by_type(world_id)

    def _spawn_boss_by_type(self, world_id: str) -> None:
        flag = WORLD_BOSS_FLAGS.get(world_id)
        if flag and self.progression_flags.get(flag):
            return

        boss_type = {
            "toxic_plains": "mecha_beast",
            "crystal_desert": "crystal_titan",
            "fungal_cave": "toxic_worm",
            "void_ruins": "void_guardian",
        }.get(world_id, "boss")

        spawn_x = self.player.x + 80
        spawn_y = self.player.y + 80
        
        self.boss_manager.spawn_boss(boss_type, spawn_x, spawn_y)
        if self.boss_manager.active_boss:
            self.bosses.append(self.boss_manager.active_boss)
            self.current_boss_spawned = True

    def _setup_portals_for_world(self, world_id: str) -> None:
        portals: list[Portal] = []

        if world_id == "toxic_plains":
            portals.append(
                Portal(
                    portal_id="portal_to_crystal",
                    x=4500,
                    y=3200,
                    target_world="crystal_desert",
                    requirement=PortalRequirement(
                        required_flag="boss_toxic_plains_defeated",
                        required_item="item_battery_core",
                        required_count=1
                    ),
                )
            )
        elif world_id == "crystal_desert":
            portals.append(
                Portal(
                    portal_id="portal_to_toxic",
                    x=500,
                    y=500,
                    target_world="toxic_plains",
                    requirement=PortalRequirement(),
                )
            )
            portals.append(
                Portal(
                    portal_id="portal_to_fungal",
                    x=5200,
                    y=3800,
                    target_world="fungal_cave",
                    requirement=PortalRequirement(required_flag="boss_crystal_desert_defeated"),
                )
            )
        elif world_id == "fungal_cave":
            portals.append(
                Portal(
                    portal_id="portal_to_crystal",
                    x=500,
                    y=500,
                    target_world="crystal_desert",
                    requirement=PortalRequirement(),
                )
            )
            portals.append(
                Portal(
                    portal_id="portal_to_void",
                    x=5800,
                    y=4200,
                    target_world="void_ruins",
                    requirement=PortalRequirement(required_flag="boss_fungal_cave_defeated"),
                )
            )
        elif world_id == "void_ruins":
            portals.append(
                Portal(
                    portal_id="portal_to_fungal",
                    x=500,
                    y=500,
                    target_world="fungal_cave",
                    requirement=PortalRequirement(),
                )
            )

        self.portal_manager.set_portals(portals)

        saved = self.portal_save_states.get(world_id)
        if saved:
            self.portal_manager.apply_save_data(saved)

    def _handle_progression_and_rewards(self) -> None:
        world_id = self.world_manager.current_world_id
        boss_flag = WORLD_BOSS_FLAGS.get(world_id)

        # Chapter 1 Boss Spawn Logic: Wait for stats to be full
        if world_id == "toxic_plains" and not self.chapter_1_boss_spawned:
            if self.player.health >= self.player.max_health and \
               self.player.oxygen >= self.player.max_oxygen and \
               self.player.hunger >= self.player.max_hunger:
                # Spawn boss right next to player
                self._spawn_boss_by_type("toxic_plains")
                self.chapter_1_boss_spawned = True
                self._set_ui_message("STATS FULL! MECHA BEAST HAS ARRIVED!", duration=5.0)

        if boss_flag and not self.progression_flags.get(boss_flag, False) and not self.bosses and self.current_boss_spawned:
            # Boss just died (flag was false, bosses list empty, but was spawned before)
            self.progression_flags[boss_flag] = True
            self.world_completion_states[world_id] = True
            self.current_boss_spawned = False
            
            # Sync with ProgressionManager
            boss_id = {
                "toxic_plains": "mecha_beast",
                "crystal_desert": "crystal_titan",
                "fungal_cave": "toxic_worm",
                "void_ruins": "void_guardian",
            }.get(world_id)
            
            if boss_id:
                reward = self.progression_manager.mark_boss_defeated(boss_id)
                # Note: mark_boss_defeated already returns the artifact ID (alpha, beta, gamma)
                    
            self._grant_world_reward(world_id)
            
            # Chapter 2, 3, 4: Spawn portal at death location
            if world_id != "toxic_plains":
                # Find death pos (using boss_manager's last spawn or we can track it)
                # For now, let's spawn it where the player is or near where the boss was
                death_x = self.player.x + 50
                death_y = self.player.y + 50
                self._spawn_progression_portal(world_id, death_x, death_y)
                
            self._set_ui_message(f"Boss defeated! Reward acquired.")

        # Update unlocked world flags
        self.progression_flags["portal_to_crystal_unlocked"] = self.progression_flags["boss_toxic_plains_defeated"]
        self.progression_flags["portal_to_fungal_unlocked"] = self.progression_flags["boss_crystal_desert_defeated"]
        self.progression_flags["portal_to_void_unlocked"] = self.progression_flags["boss_fungal_cave_defeated"]

        # Sync unlocked worlds
        if self.progression_flags["portal_to_crystal_unlocked"]: self.progression_manager.unlocked_worlds.add("crystal_desert")
        if self.progression_flags["portal_to_fungal_unlocked"]: self.progression_manager.unlocked_worlds.add("fungal_cave")
        if self.progression_flags["portal_to_void_unlocked"]: self.progression_manager.unlocked_worlds.add("void_ruins")

        if self.progression_flags["boss_toxic_plains_defeated"]:
            self.player.disable_survival_drain = True

    def _spawn_progression_portal(self, world_id: str, x: float, y: float) -> None:
        target_map = {
            "crystal_desert": "fungal_cave",
            "fungal_cave": "void_ruins",
            "void_ruins": "toxic_plains"
        }
        target = target_map.get(world_id)
        if not target: return
        
        new_portal = Portal(
            portal_id=f"exit_{world_id}",
            x=x,
            y=y,
            target_world=target,
            requirement=PortalRequirement()
        )
        # Force unlock it immediately as it appeared from boss
        new_portal.is_unlocked = True
        self.portal_manager.portals.append(new_portal)
        self._set_ui_message(f"A portal to {target} has appeared!")

    def _grant_world_reward(self, world_id: str) -> None:
        if world_id == "toxic_plains":
            self.inventory.add_item("item_battery_core", 1)
            self._set_ui_message("Acquired Battery Core. Find the Abandoned Base.")
        elif world_id == "crystal_desert":
            self.inventory.add_item("quest_artifact_alpha", 1)
            self.artifact_tracking["alpha"] = True
            self.npcs.append(NPC(self.player.x + 100, self.player.y))
        elif world_id == "fungal_cave":
            self.inventory.add_item("quest_artifact_beta", 1)
            self.artifact_tracking["beta"] = True
            self.npcs.append(NPC(self.player.x + 100, self.player.y))
        elif world_id == "void_ruins":
            self.inventory.add_item("quest_artifact_gamma", 1)
            self.artifact_tracking["gamma"] = True
            self.npcs.append(NPC(self.player.x + 100, self.player.y))

    def _handle_pending_actions(self) -> None:
        if self.pending_use_hotbar:
            self.pending_use_hotbar = False
            self._use_selected_hotbar_item()

        if self.pending_portal_interact:
            self.pending_portal_interact = False
            self._interact()

        if self.pending_save:
            self.pending_save = False
            self._save_game(slot=0)

        if self.pending_load:
            self.pending_load = False
            self._load_game(slot=0)
            self._load_game(slot=0)

    def _interact(self) -> None:
        import math
        # Check Endgame Ship Interaction
        if self.world_manager.current_world_id == "toxic_plains":
            if math.hypot(self.player.x - 1000, self.player.y - 1000) < 150:
                if self.inventory.has_item("ship_repair_kit", 1):
                    self.ship_repair_prompt_active = True
                    self._set_ui_message("ORION-7 REPAIRED? [Y/N]", duration=10.0)
                else:
                    self._set_ui_message("ORION-7 is critically damaged. Needs a Ship Repair Kit.")
                return

        # Check NPC interaction
        for npc in self.npcs:
            if math.hypot(self.player.x - npc.x, self.player.y - npc.y) < 100:
                world_id = self.world_manager.current_world_id
                if world_id in ["crystal_desert", "fungal_cave"]:
                    if self.inventory.has_item("item_meteor_ore", 15):
                        # Simple logic: Upgrade gun first, then pickaxe
                        if not self.inventory.has_item("weapon_plasma_gun", 1):
                            if self.trading_system.trade_for_upgrade_gun():
                                self._set_ui_message("Upgraded to Plasma Gun!")
                        elif not self.inventory.has_item("tool_crystal_pickaxe", 1):
                            if self.trading_system.trade_for_upgrade_pickaxe():
                                self._set_ui_message("Upgraded to Crystal Pickaxe!")
                        else:
                            self._set_ui_message("You already have all upgrades from me.")
                    else:
                        self._set_ui_message("NPC: 'I need 15 Meteor Ore for upgrades.'")
                elif world_id == "void_ruins":
                    if self.trading_system.perform_trade_for_repair_kit():
                        self._set_ui_message("Received Ship Repair Kit! Return to Chapter 1.")
                    else:
                        self._set_ui_message("NPC: 'Collect 3 Mystery Items to get the Repair Kit.'")
                return

        portal = self.portal_manager.get_near_portal(self.player.x, self.player.y)
        if portal is None:
            self._set_ui_message("Nothing nearby to interact with")
            return

        if not portal.is_unlocked:
            if portal.try_unlock(self.progression_flags, self.inventory):
                self._set_ui_message("Portal unlocked")
            else:
                self._set_ui_message("Portal remains locked")
                return

        # Show teleport prompt
        self.portal_confirm_prompt_active = True
        self.active_portal_target = portal.target_world
        self._set_ui_message(f"Teleport to {portal.target_world}? [Y/N]", duration=10.0)

    def _handle_confirmation_choice(self, choice: bool) -> None:
        if self.ship_repair_prompt_active:
            if choice:
                self._set_ui_message("ORION-7 REPAIRED! PREPARING FOR LAUNCH...", duration=5.0)
                self.engine.state_machine.change_state("Ending")
            else:
                self._set_ui_message("Repair cancelled.")
            self.ship_repair_prompt_active = False
            return

        if self.portal_confirm_prompt_active:
            if choice and self.active_portal_target:
                self._transition_world(self.active_portal_target)
            else:
                self._set_ui_message("Teleport cancelled.")
            self.portal_confirm_prompt_active = False
            self.active_portal_target = None
            return

    def _transition_world(self, target_world: str) -> None:
        current_world = self.world_manager.current_world_id
        self.portal_save_states[current_world] = self.portal_manager.to_save_data()
        self.ore_save_states[current_world] = self._serialize_ores_for_world(current_world)

        self.world_manager.transition_world(target_world)
        self.hazard_manager = HazardManager(self.world_manager.seed)

        self.player.x = 1000
        self.player.y = 1000
        self.player.rect.center = (int(self.player.x), int(self.player.y))
        self.player.hitbox.update(self.player.x, self.player.y)

        self.spawn_manager = SpawnManager()
        self._refresh_world_entities()

        self.camera.offset.x = self.player.x - WINDOW_WIDTH * 0.5
        self.camera.offset.y = self.player.y - WINDOW_HEIGHT * 0.5

        self._set_ui_message(f"Transitioned to {target_world}")

    def _serialize_ores_for_world(self, world_id: str) -> dict[str, dict]:
        state: dict[str, dict] = {}
        for chunk_ores in self.spawn_manager.ores_by_chunk.values():
            for ore in chunk_ores:
                state[ore.node_id] = ore.to_save_data()
        return state

    def _apply_saved_ore_states(self) -> None:
        world_id = self.world_manager.current_world_id
        if world_id not in self.ore_save_states:
            return

        state_map = self.ore_save_states[world_id]
        for ore in self.visible_ores:
            payload = state_map.get(ore.node_id)
            if not payload:
                continue
            if getattr(ore, "_state_applied", False):
                continue
            ore.load_save_data(payload)
            ore._state_applied = True

    def _use_selected_hotbar_item(self) -> None:
        slot = self.inventory.get_hotbar_slot()
        if slot is None:
            self._set_ui_message("No item selected")
            return

        item = ItemDatabase.get_item(slot.item_id)
        if item is None or item.type != "consumable":
            self._set_ui_message("Selected slot is not consumable")
            return

        cooldown = self.consumable_cooldowns.get(item.id, 0.0)
        if cooldown > 0:
            self._set_ui_message(f"{item.name} cooldown {cooldown:.1f}s")
            return

        effects = item.consumable_effects
        heal = float(effects.get("heal", 0))
        oxygen = float(effects.get("oxygen", 0))
        hunger = float(effects.get("hunger", 0))

        self.player.health = min(self.player.max_health, self.player.health + heal)
        self.player.oxygen = min(self.player.max_oxygen, self.player.oxygen + oxygen)
        self.player.hunger = min(self.player.max_hunger, self.player.hunger + hunger)

        consumed = self.inventory.consume_selected_hotbar_item(1)
        if consumed:
            self.consumable_cooldowns[item.id] = float(effects.get("cooldown", 1.5))
            self._set_ui_message(f"Used {item.name}")

    def _craft_selected_recipe(self) -> None:
        recipes = self._get_active_recipes()
        if not recipes:
            self._set_ui_message("No recipe")
            return

        recipe = recipes[self.selected_recipe_index]
        ok, info = self.crafting.craft(recipe.recipe_id, self.inventory)
        if ok:
            self._set_ui_message(f"Crafted {recipe.name}")
        else:
            self._set_ui_message(info)

    def _cycle_recipe_category(self, delta: int) -> None:
        if not self.recipe_categories:
            return
        current_idx = self.recipe_categories.index(self.active_recipe_category)
        current_idx = (current_idx + delta) % len(self.recipe_categories)
        self.active_recipe_category = self.recipe_categories[current_idx]
        self.selected_recipe_index = 0

    def _get_active_recipes(self):
        recipes = self.crafting.get_recipes_by_category(self.active_recipe_category)
        if recipes:
            return recipes
        return self.crafting.recipes

    def _tick_consumable_cooldowns(self, dt: float) -> None:
        expired = []
        for item_id in self.consumable_cooldowns:
            self.consumable_cooldowns[item_id] = max(0.0, self.consumable_cooldowns[item_id] - dt)
            if self.consumable_cooldowns[item_id] <= 0:
                expired.append(item_id)
        for item_id in expired:
            self.consumable_cooldowns.pop(item_id, None)

    def _handle_inventory_mouse(self, event) -> None:
        if event.type != pygame.MOUSEBUTTONDOWN:
            return

        hit = self._inventory_slot_from_mouse(event.pos)

        if event.button == 1:
            if hit is None:
                return
            hit_type, idx = hit
            if self.inventory.drag_payload is None:
                self.inventory.begin_drag(hit_type, idx)
            else:
                self.inventory.drop_drag(hit_type, idx)

        if event.button == 3 and hit and hit[0] == "inventory":
            src = hit[1]
            stack = self.inventory.slots[src]
            if stack and stack.count > 1:
                free = None
                for i, slot in enumerate(self.inventory.slots):
                    if slot is None:
                        free = i
                        break
                if free is not None:
                    self.inventory.split_stack(src, free, stack.count // 2)

    def _inventory_slot_from_mouse(self, mouse_pos):
        mx, my = mouse_pos

        start_x = 30
        start_y = WINDOW_HEIGHT - 320
        slot_size = 46
        gap = 6

        for idx in range(self.inventory.slot_count):
            col = idx % self.inventory.grid_cols
            row = idx // self.inventory.grid_cols
            x = start_x + col * (slot_size + gap)
            y = start_y + row * (slot_size + gap)
            rect = pygame.Rect(x, y, slot_size, slot_size)
            if rect.collidepoint(mx, my):
                return ("inventory", idx)

        eq_start_x = start_x + self.inventory.grid_cols * (slot_size + gap) + 25
        eq_start_y = start_y
        for i, key in enumerate(self.inventory.equipment.keys()):
            rect = pygame.Rect(eq_start_x, eq_start_y + i * (slot_size + gap), slot_size, slot_size)
            if rect.collidepoint(mx, my):
                return ("equipment", key)

        return None

    def _save_game(self, slot: int) -> None:
        current_world = self.world_manager.current_world_id
        self.portal_save_states[current_world] = self.portal_manager.to_save_data()
        self.ore_save_states[current_world] = self._serialize_ores_for_world(current_world)

        all_ore_states = []
        for world_id, node_map in self.ore_save_states.items():
            for node_id, payload in node_map.items():
                state = dict(payload)
                state["world_id"] = world_id
                state["node_id"] = node_id
                all_ore_states.append(state)

        self.save_manager.save_game(
            slot=slot,
            player=self.player,
            inventory=self.inventory,
            crafted_items=self.crafting.to_save_data(),
            unlocked_portals=self.portal_save_states,
            current_world=current_world,
            mined_ores=all_ore_states,
            biome_states={world_id: states for world_id, states in self.world_completion_states.items()},
            progression_flags=self.progression_flags,
            status_effects=self.status_effects.to_save_data(),
            progression_data={"unlocked_worlds": list(self.progression_manager.unlocked_worlds),
                              "defeated_bosses": list(self.progression_manager.defeated_bosses),
                              "collected_artifacts": list(self.progression_manager.collected_artifacts),
                              "has_ship_repair_kit": self.progression_manager.has_ship_repair_kit}
        )
        self._set_ui_message("Saved game")

    def _load_game(self, slot: int) -> None:
        payload = self.save_manager.load_game(slot, self.player, self.inventory)
        if payload is None:
            self._set_ui_message("No save slot found")
            return

        self.crafting.load_save_data(payload.get("crafted_items", {}))
        self.progression_flags.update(payload.get("progression_flags", {}))
        self.world_completion_states.update(payload.get("biome_states", {}))
        self.status_effects.load_save_data(payload.get("status_effects", []))
        self.progression_manager.load_progression(payload)

        portals_payload = payload.get("unlocked_portals", {})
        if isinstance(portals_payload, dict):
            self.portal_save_states = portals_payload

        self.ore_save_states.clear()
        for ore in payload.get("mined_ores", []):
            world_id = ore.get("world_id", self.world_manager.current_world_id)
            self.ore_save_states.setdefault(world_id, {})[ore.get("node_id", "")] = ore

        target_world = payload.get("current_world", "toxic_plains")
        self.world_manager.transition_world(target_world)
        self.hazard_manager = HazardManager(self.world_manager.seed)
        self.spawn_manager = SpawnManager()
        self._refresh_world_entities()

        self._set_ui_message("Loaded save")

    def _render_grid(self, surface: pygame.Surface, ox: int, oy: int) -> None:
        start_x = (ox // TILE_SIZE) * TILE_SIZE
        start_y = (oy // TILE_SIZE) * TILE_SIZE
        end_x = ox + WINDOW_WIDTH + TILE_SIZE
        end_y = oy + WINDOW_HEIGHT + TILE_SIZE

        for gx in range(start_x, end_x, TILE_SIZE):
            for gy in range(start_y, end_y, TILE_SIZE):
                r = pygame.Rect(gx - ox, gy - oy, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(surface, _GRID_LINE_CLR, r, 1)

    def _render_debug(self, surface: pygame.Surface, ox: int, oy: int) -> None:
        self.player.render_debug(surface, ox, oy)
        for enemy in self.enemies:
            enemy.render_debug(surface, ox, oy)
        for boss in self.bosses:
            boss.render_debug(surface, ox, oy)

        self.projectile_pool.render_debug(surface, ox, oy)

        for portal in self.portal_manager.portals:
            px = int(portal.x - ox)
            py = int(portal.y - oy)
            pygame.draw.circle(surface, (220, 220, 255), (px, py), 40, 1)
        
        # AI debug visualization
        any_auto = self.engine.auto_mine or self.engine.auto_combat_entities or self.engine.auto_combat_boss
        if any_auto and hasattr(self, 'ai_controller'):
            pass # Skipping drawing AI debug for brevity

        status_lines = self.status_effects.debug_lines()
        
        # New Debug Info
        progression_info = [
            f"Worlds: {', '.join(self.progression_manager.unlocked_worlds)}",
            f"Bosses Dead: {', '.join(self.progression_manager.defeated_bosses)}",
            f"Artifacts: {', '.join(self.progression_manager.collected_artifacts)}",
            f"Objective: {self.objective_system.get_current_objective()}",
        ]
        
        info_lines = [
            f"FPS: {int(self.engine.clock.get_fps())}",
            f"World: {self.world_manager.current_world_id}",
            f"Biome Chunks: {len(self.loaded_chunk_keys)}",
            f"Enemies: {len(self.enemies)} / {self.spawn_manager.max_enemies}",
            f"Ores: {len(self.visible_ores)}",
            f"Hazards: {len(self.visible_hazards)}",
            f"Portals: {len(self.portal_manager.portals)}",
            f"Inventory used: {sum(1 for s in self.inventory.slots if s is not None)}/{self.inventory.slot_count}",
        ] + status_lines + progression_info

        for i, line in enumerate(info_lines):
            surf = self.font.render(line, True, COLOR_DEBUG)
            surface.blit(surf, (10, 80 + i * 18))

    def _render_progression_debug(self, surface: pygame.Surface) -> None:
        """Renders progression flags and states for debugging."""
        debug_font = pygame.font.SysFont(None, 18)
        y_offset = 10
        
        # World Unlocks
        text = f"Worlds Unlocked: {list(self.progression_manager.unlocked_worlds)}"
        surf = debug_font.render(text, True, (0, 255, 0))
        surface.blit(surf, (10, y_offset))
        y_offset += 20
        
        # Bosses Defeated
        text = f"Bosses Defeated: {list(self.progression_manager.defeated_bosses)}"
        surf = debug_font.render(text, True, (0, 255, 0))
        surface.blit(surf, (10, y_offset))
        y_offset += 20
        
        # Artifacts
        text = f"Artifacts: {list(self.progression_manager.collected_artifacts)}"
        surf = debug_font.render(text, True, (0, 255, 0))
        surface.blit(surf, (10, y_offset))
        y_offset += 20
        
        # Current Objective
        obj = self.objective_system.get_current_objective()
        text = f"Current Obj: {obj}"
        surf = debug_font.render(text, True, (255, 255, 0))
        surface.blit(surf, (10, y_offset))

    def _render_hud(self, surface: pygame.Surface) -> None:
        self.hud.render(surface, self.player)
        self.boss_healthbar.render(surface)

        selected = self.inventory.get_hotbar_slot()
        selected_name = "None"
        if selected:
            item = ItemDatabase.get_item(selected.item_id)
            selected_name = item.name if item else selected.item_id

        hints = [
            "WASD: Move",
            "LMB: Melee",
            "Shift+LMB: Mine",
            "RMB: Shoot",
            "E: Inventory",
            "C: Crafting",
            "R: Use Hotbar",
            "F: Portal Interact",
            "F5/F9: Save/Load",
            f"Hotbar: {self.inventory.selected_hotbar + 1} ({selected_name})",
        ]

        for i, h in enumerate(hints):
            hs = self.font.render(h, True, (85, 85, 95))
            surface.blit(hs, (WINDOW_WIDTH - hs.get_width() - 12, WINDOW_HEIGHT - (len(hints) - i) * 18 - 8))

        if self.current_hazard_zone:
            hz = self.font.render(f"Hazard: {self.current_hazard_zone.hazard_type}", True, (255, 120, 90))
            surface.blit(hz, (12, 12))

        self.objective_system.render_ui(surface, self.font, 12, 40)

        mining_feedback = self.mining_system.get_feedback()
        if mining_feedback:
            mf = self.font.render(mining_feedback, True, (180, 255, 180))
            surface.blit(mf, (WINDOW_WIDTH // 2 - mf.get_width() // 2, WINDOW_HEIGHT - 26))

        if self.ui_message_timer > 0:
            msg = self.font_large.render(self.ui_message, True, (240, 240, 200))
            surface.blit(msg, (WINDOW_WIDTH // 2 - msg.get_width() // 2, 56))

    def _render_inventory(self, surface: pygame.Surface) -> None:
        panel = pygame.Surface((520, 300), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 180))
        surface.blit(panel, (20, WINDOW_HEIGHT - 340))

        title = self.font.render("Inventory", True, (220, 220, 255))
        surface.blit(title, (30, WINDOW_HEIGHT - 334))

        start_x = 30
        start_y = WINDOW_HEIGHT - 320
        slot_size = 46
        gap = 6

        mouse_pos = pygame.mouse.get_pos()
        self.tooltip_text = ""

        for idx in range(self.inventory.slot_count):
            col = idx % self.inventory.grid_cols
            row = idx // self.inventory.grid_cols
            x = start_x + col * (slot_size + gap)
            y = start_y + row * (slot_size + gap)
            rect = pygame.Rect(x, y, slot_size, slot_size)

            is_hotbar = idx < self.inventory.hotbar_size
            border = (140, 140, 80) if is_hotbar else (90, 90, 100)
            if idx == self.inventory.selected_hotbar:
                border = (255, 220, 100)

            pygame.draw.rect(surface, (38, 38, 48), rect)
            pygame.draw.rect(surface, border, rect, 2)

            stack = self.inventory.slots[idx]
            if stack:
                item = ItemDatabase.get_item(stack.item_id)
                color = (160, 180, 220)
                if item:
                    color = self._rarity_color(item.rarity)
                item_rect = rect.inflate(-12, -12)
                pygame.draw.rect(surface, color, item_rect)

                count_text = self.font.render(str(stack.count), True, (255, 255, 255))
                surface.blit(count_text, (rect.right - count_text.get_width() - 4, rect.bottom - 18))

                if stack.durability is not None:
                    max_dur = 1
                    item_data = ItemDatabase.get_item(stack.item_id)
                    if item_data:
                        max_dur = int(item_data.tool_stats.get("durability", 1))
                    ratio = max(0.0, min(1.0, stack.durability / max(1, max_dur)))
                    pygame.draw.rect(surface, (45, 45, 45), (rect.x + 4, rect.y + 4, rect.width - 8, 4))
                    pygame.draw.rect(surface, (120, 240, 120), (rect.x + 4, rect.y + 4, int((rect.width - 8) * ratio), 4))

                if rect.collidepoint(mouse_pos):
                    desc = item.description if item else stack.item_id
                    self.tooltip_text = f"{item.name if item else stack.item_id} - {desc}"

        eq_start_x = start_x + self.inventory.grid_cols * (slot_size + gap) + 25
        eq_start_y = start_y
        for i, key in enumerate(self.inventory.equipment.keys()):
            rect = pygame.Rect(eq_start_x, eq_start_y + i * (slot_size + gap), slot_size, slot_size)
            pygame.draw.rect(surface, (35, 35, 44), rect)
            pygame.draw.rect(surface, (120, 120, 160), rect, 2)
            label = self.font.render(key[:1].upper(), True, (180, 180, 220))
            surface.blit(label, (rect.x + 3, rect.y + 2))

            stack = self.inventory.equipment[key]
            if stack:
                item = ItemDatabase.get_item(stack.item_id)
                pygame.draw.rect(surface, self._rarity_color(item.rarity if item else "Common"), rect.inflate(-12, -12))

        if self.inventory.drag_payload:
            drag = self.inventory.drag_payload.stack
            rect = pygame.Rect(mouse_pos[0] - 14, mouse_pos[1] - 14, 28, 28)
            pygame.draw.rect(surface, (230, 230, 120), rect)
            cnt = self.font.render(str(drag.count), True, (20, 20, 20))
            surface.blit(cnt, (rect.right - cnt.get_width(), rect.bottom - 16))

        if self.tooltip_text:
            tip = self.font.render(self.tooltip_text, True, (250, 250, 250))
            tip_bg = pygame.Surface((tip.get_width() + 12, 24), pygame.SRCALPHA)
            tip_bg.fill((0, 0, 0, 190))
            tx = min(WINDOW_WIDTH - tip_bg.get_width() - 8, mouse_pos[0] + 14)
            ty = max(8, mouse_pos[1] - 28)
            surface.blit(tip_bg, (tx, ty))
            surface.blit(tip, (tx + 6, ty + 4))

    def _render_crafting(self, surface: pygame.Surface) -> None:
        panel = pygame.Surface((390, 300), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 180))
        x = WINDOW_WIDTH - 410
        y = WINDOW_HEIGHT - 340
        surface.blit(panel, (x, y))

        title = self.font.render(f"Crafting [{self.active_recipe_category}]", True, (220, 255, 220))
        surface.blit(title, (x + 10, y + 8))

        recipes = self._get_active_recipes()
        if self.selected_recipe_index >= len(recipes):
            self.selected_recipe_index = max(0, len(recipes) - 1)

        for i, recipe in enumerate(recipes[:10]):
            color = (255, 255, 120) if i == self.selected_recipe_index else (210, 210, 220)
            can_craft = self.crafting.can_craft(recipe.recipe_id, self.inventory)
            if not can_craft:
                color = (150, 140, 140) if i != self.selected_recipe_index else (220, 170, 120)

            line = f"{recipe.name} -> {recipe.result_count}"
            txt = self.font.render(line, True, color)
            surface.blit(txt, (x + 12, y + 38 + i * 24))

        help_text = [
            "Up/Down: Select",
            "Enter: Craft",
            "Q/W: Category",
            "C: Close",
        ]
        for i, line in enumerate(help_text):
            txt = self.font.render(line, True, (130, 180, 150))
            surface.blit(txt, (x + 12, y + 246 + i * 16))

    def _set_ui_message(self, text: str, duration: float = 1.8) -> None:
        self.ui_message = text
        self.ui_message_timer = duration

    def _tick_ui(self, dt: float) -> None:
        if self.ui_message_timer > 0:
            self.ui_message_timer = max(0.0, self.ui_message_timer - dt)

    @staticmethod
    def _rarity_color(rarity: str) -> tuple[int, int, int]:
        table = {
            "Common": (165, 165, 175),
            "Uncommon": (95, 200, 120),
            "Rare": (95, 155, 255),
            "Epic": (190, 100, 255),
            "Legendary": (255, 180, 80),
        }
        return table.get(rarity, (180, 180, 180))
