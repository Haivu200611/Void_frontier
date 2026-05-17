import pygame
from settings import *
from core.state_machine import StateMachine

from states.menu_state import MenuState
from states.play_state import PlayState
from states.how_to_play_state import HowToPlayState
from states.ending_state import EndingState
from states.game_over_state import GameOverState
from states.language_menu_state import LanguageMenuState
from states.intro_state import IntroState
from states.outtro_state import OuttroState

class GameEngine:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Global game flags
        self.debug_mode = DEBUG_MODE
        self.auto_mine = False
        self.auto_combat_entities = False
        self.auto_combat_boss = False
        
        # Initialize State Machine
        self.state_machine = StateMachine(self)
        self._register_states()
        
        # Start game at Menu
        self.state_machine.change_state("Menu")
        
    def _register_states(self):
        self.state_machine.add_state("Menu", MenuState)
        self.state_machine.add_state("Intro", IntroState)
        self.state_machine.add_state("Play", PlayState)
        self.state_machine.add_state("HowToPlay", HowToPlayState)
        self.state_machine.add_state("LanguageMenu", LanguageMenuState)
        self.state_machine.add_state("Ending", EndingState)
        self.state_machine.add_state("Outtro", OuttroState)
        self.state_machine.add_state("GameOver", GameOverState)
        
    def handle_events(self):
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F1:
                    self.debug_mode = not self.debug_mode
                    
        self.state_machine.handle_events(events)
        
    def update(self, dt):
        self.state_machine.update(dt)
        
    def render(self):
        self.screen.fill(COLOR_BG)
        self.state_machine.render(self.screen)
        
        if self.debug_mode:
            self._render_debug()
            
        pygame.display.flip()
        
    def _render_debug(self):
        font = pygame.font.SysFont(None, 24)
        fps_text = font.render(f"FPS: {int(self.clock.get_fps())}", True, COLOR_DEBUG)
        mine_text = font.render(f"AUTO MINE: {'ON' if self.auto_mine else 'OFF'} (M)", True, (100, 255, 100) if self.auto_mine else COLOR_DEBUG)
        combat_text = font.render(f"AUTO ENTITIES: {'ON' if self.auto_combat_entities else 'OFF'} (K)", True, (100, 255, 255) if self.auto_combat_entities else COLOR_DEBUG)
        boss_text = font.render(f"AUTO BOSS: {'ON' if self.auto_combat_boss else 'OFF'} (B)", True, (255, 100, 100) if self.auto_combat_boss else COLOR_DEBUG)
        debug_text = font.render(f"DEBUG: ON (F1)", True, COLOR_DEBUG)
        
        self.screen.blit(fps_text, (10, 10))
        self.screen.blit(mine_text, (10, 30))
        self.screen.blit(combat_text, (10, 50))
        self.screen.blit(boss_text, (10, 70))
        self.screen.blit(debug_text, (10, 90))
        
        # Show AI debug info if any auto mode is on
        any_auto = self.auto_mine or self.auto_combat_entities or self.auto_combat_boss
        if any_auto and hasattr(self.state_machine.current_state, 'ai_controller'):
            ai_debug = self.state_machine.current_state.ai_controller.get_debug_info()
            
            small_font = pygame.font.SysFont(None, 20)
            y_offset = 80
            
            debug_lines = [
                f"Goal: {ai_debug.get('current_goal', 'None')}",
                f"Action: {ai_debug.get('current_action', 'Idle')}",
                f"Threat: {ai_debug.get('threat_level', 0):.2f}",
                f"Active Goals: {ai_debug.get('active_goals', 0)}",
                f"Path Length: {ai_debug.get('path_length', 0)}",
                f"Explored Chunks: {ai_debug.get('explored_chunks', 0)}",
            ]
            
            for line in debug_lines:
                text = small_font.render(line, True, (100, 200, 100))
                self.screen.blit(text, (10, y_offset))
                y_offset += 20
        
    def run(self):
        while self.running:
            # Calculate delta time (dt) in seconds
            dt = self.clock.tick(FPS) / 1000.0
            
            self.handle_events()
            self.update(dt)
            self.render()
