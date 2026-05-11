"""
Playtest tools for development and debugging.
Provides console commands, test scenarios, and debug features.
"""

from typing import Dict, Callable, Optional, List


class PlaytestConsole:
    """
    In-game debug console for testing and development.
    Can execute commands like: spawn_enemy, god_mode, noclip, etc.
    """
    
    def __init__(self):
        self.open = False
        self.commands: Dict[str, Callable] = {}
        self.command_history: List[str] = []
        self.history_index = 0
        self.input_text = ""
        self.output_text = ""
        self._register_commands()
    
    def _register_commands(self) -> None:
        """Register available commands."""
        self.commands = {
            'help': self._cmd_help,
            'spawn_enemy': self._cmd_spawn_enemy,
            'spawn_boss': self._cmd_spawn_boss,
            'god_mode': self._cmd_god_mode,
            'heal': self._cmd_heal,
            'teleport': self._cmd_teleport,
            'spawn_particles': self._cmd_spawn_particles,
            'test_hit': self._cmd_test_hit,
            'reset': self._cmd_reset,
            'clear': self._cmd_clear,
        }
    
    def toggle_open(self) -> None:
        """Toggle console open/closed."""
        self.open = not self.open
    
    def handle_input(self, event, play_state=None) -> bool:
        """Handle console input."""
        if not self.open:
            return False
        
        import pygame
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.execute_command(self.input_text, play_state=play_state)
                self.command_history.append(self.input_text)
                self.history_index = len(self.command_history)
                self.input_text = ""
                return True
            
            elif event.key == pygame.K_UP:
                if self.history_index > 0:
                    self.history_index -= 1
                    self.input_text = self.command_history[self.history_index]
                return True
            
            elif event.key == pygame.K_DOWN:
                if self.history_index < len(self.command_history) - 1:
                    self.history_index += 1
                    self.input_text = self.command_history[self.history_index]
                elif self.history_index == len(self.command_history) - 1:
                    self.history_index += 1
                    self.input_text = ""
                return True
            
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
                return True
            
            elif event.key == pygame.K_ESCAPE:
                self.toggle_open()
                return True
            
            elif event.unicode:
                self.input_text += event.unicode
                return True
        
        return False
    
    def execute_command(self, cmd_str: str, play_state=None) -> None:
        """Execute a command string."""
        parts = cmd_str.strip().split()
        if not parts:
            return
        
        cmd_name = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        if cmd_name in self.commands:
            try:
                result = self.commands[cmd_name](play_state, *args)
                self.output_text = result if result else "Command executed"
            except Exception as e:
                self.output_text = f"Error: {str(e)}"
        else:
            self.output_text = f"Unknown command: {cmd_name}. Type 'help' for commands."
    
    def _cmd_help(self, play_state, *args) -> str:
        """Show help."""
        return f"Available commands: {', '.join(sorted(self.commands.keys()))}"
    
    def _cmd_spawn_enemy(self, play_state, *args) -> str:
        """Spawn an enemy. Usage: spawn_enemy [count]"""
        if not play_state: return "Error: PlayState not linked"
        count = int(args[0]) if args else 1
        for _ in range(count):
            play_state.spawn_manager.spawn_enemy(play_state.player, play_state.enemies, play_state.enemy_ais)
        return f"Spawning {count} enemies"
    
    def _cmd_spawn_boss(self, play_state, *args) -> str:
        """Spawn a boss. Usage: spawn_boss [type]"""
        if not play_state: return "Error: PlayState not linked"
        boss_type = args[0] if args else "mecha_beast"
        play_state.boss_manager.spawn_boss(boss_type, play_state.player.x + 200, play_state.player.y)
        if play_state.boss_manager.active_boss:
            play_state.bosses.append(play_state.boss_manager.active_boss)
        return f"Spawning boss: {boss_type}"
    
    def _cmd_god_mode(self, play_state, *args) -> str:
        """Enable/disable god mode."""
        if not play_state: return "Error: PlayState not linked"
        play_state.player.hurtbox.grant_invincibility(9999)
        return "God mode enabled (invincibility)"
    
    def _cmd_heal(self, play_state, *args) -> str:
        """Heal player. Usage: heal [amount]"""
        if not play_state: return "Error: PlayState not linked"
        amount = int(args[0]) if args else 100
        play_state.player.heal(amount)
        return f"Healing {amount} HP"
    
    def _cmd_teleport(self, play_state, *args) -> str:
        """Teleport player. Usage: teleport <x> <y>"""
        if not play_state: return "Error: PlayState not linked"
        if len(args) < 2:
            return "Usage: teleport <x> <y>"
        x, y = float(args[0]), float(args[1])
        play_state.player.x = x
        play_state.player.y = y
        return f"Teleporting to ({x}, {y})"
    
    def _cmd_spawn_particles(self, play_state, *args) -> str:
        """Spawn particles. Usage: spawn_particles [type] [count]"""
        if not play_state: return "Error: PlayState not linked"
        particle_type = args[0] if args else "hit"
        count = int(args[1]) if len(args) > 1 else 1
        for _ in range(count):
            if particle_type == "hit": play_state.particle_system.spawn_hit_particles(play_state.player.x, play_state.player.y)
            elif particle_type == "explosion": play_state.particle_system.spawn_explosion_particles(play_state.player.x, play_state.player.y)
            elif particle_type == "toxic": play_state.particle_system.spawn_toxic_particles(play_state.player.x, play_state.player.y)
        return f"Spawning {count} {particle_type} particles"
    
    def _cmd_test_hit(self, play_state, *args) -> str:
        """Test hit effect."""
        if not play_state: return "Error: PlayState not linked"
        play_state.screen_effects.trigger_heavy_hit()
        return "Testing hit effect"
    
    def _cmd_reset(self, play_state, *args) -> str:
        """Reset player to starting position."""
        if not play_state: return "Error: PlayState not linked"
        play_state.player.x = 1000
        play_state.player.y = 1000
        return "Player reset"
    
    def _cmd_clear(self, *args) -> str:
        """Clear console output."""
        self.output_text = ""
        return ""
    
    def render(self, surface, font) -> None:
        """Render console overlay."""
        if not self.open:
            return
        
        # Semi-transparent background
        overlay = __import__('pygame').Surface((surface.get_width(), 300))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(220)
        surface.blit(overlay, (0, 0))
        
        # Title
        title = font.render("Debug Console", True, (0, 255, 0))
        surface.blit(title, (10, 10))
        
        # Output
        output_lines = self.output_text.split('\n')[:3]
        y = 40
        for line in output_lines:
            text = font.render(line, True, (200, 200, 200))
            surface.blit(text, (10, y))
            y += 22
        
        # Input
        input_text = f"> {self.input_text}"
        input_surface = font.render(input_text, True, (0, 255, 0))
        surface.blit(input_surface, (10, 260))


class TestScenarios:
    """Pre-defined test scenarios for playtesting."""
    
    @staticmethod
    def scenario_combat_stress(play_state) -> None:
        """Spawn many enemies for combat stress testing."""
        from tools.profiler import DebugSpawner
        DebugSpawner.spawn_test_entities(play_state, 20)
        play_state.audio_manager.play_sfx("attack_melee.wav")
    
    @staticmethod
    def scenario_boss_rush(play_state) -> None:
        """Spawn boss for testing."""
        from tools.profiler import DebugSpawner
        DebugSpawner.spawn_boss(play_state, "mecha_beast")
    
    @staticmethod
    def scenario_particle_stress(play_state) -> None:
        """Test particle system with many effects."""
        import random
        for _ in range(20):
            x = play_state.player.x + random.randint(-300, 300)
            y = play_state.player.y + random.randint(-300, 300)
            play_state.particle_system.spawn_hit_particles(x, y)
    
    @staticmethod
    def scenario_audio_test(play_state) -> None:
        """Test audio system."""
        play_state.audio_manager.play_sfx("attack_melee.wav")
        play_state.audio_manager.play_ui_sound("button_click.wav")
    
    @staticmethod
    def scenario_visual_effects(play_state) -> None:
        """Test visual effects."""
        play_state.screen_effects.trigger_heavy_hit()
    
    @staticmethod
    def scenario_slow_motion(play_state) -> None:
        """Test slow motion."""
        play_state.screen_effects.slow_motion.trigger(0.2, 1.0)
    
    @staticmethod
    def scenario_all_effects(play_state) -> None:
        """Test all effects at once."""
        play_state.particle_system.spawn_explosion_particles(play_state.player.x, play_state.player.y)
        play_state.screen_effects.trigger_explosion()
        play_state.audio_manager.play_sfx("attack_melee.wav")


# Global console instance
_console: Optional[PlaytestConsole] = None

def get_playtest_console() -> PlaytestConsole:
    """Get or create global console."""
    global _console
    if _console is None:
        _console = PlaytestConsole()
    return _console
