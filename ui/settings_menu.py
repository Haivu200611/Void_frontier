import pygame
from typing import List, Callable, Optional
from settings import *


class MenuItem:
    """A single menu item."""
    
    def __init__(self, label: str, value=None, callback: Optional[Callable] = None):
        self.label = label
        self.value = value
        self.callback = callback
        self.rect = None
        self.hovered = False
        self.active = False


class Slider:
    """A slider control for numeric values."""
    
    def __init__(self, label: str, min_val: float, max_val: float, current_val: float,
                 on_change: Optional[Callable] = None):
        self.label = label
        self.min_val = min_val
        self.max_val = max_val
        self.current_val = current_val
        self.on_change = on_change
        
        self.rect = None
        self.slider_rect = None
        self.hovered = False
        self.dragging = False
    
    def set_value(self, val: float) -> None:
        """Set slider value."""
        self.current_val = max(self.min_val, min(self.max_val, val))
        if self.on_change:
            self.on_change(self.current_val)
    
    def get_normalized(self) -> float:
        """Get value as 0-1."""
        if self.max_val == self.min_val:
            return 0.0
        return (self.current_val - self.min_val) / (self.max_val - self.min_val)


class Toggle:
    """A toggle/checkbox control."""
    
    def __init__(self, label: str, enabled: bool = False, on_change: Optional[Callable] = None):
        self.label = label
        self.enabled = enabled
        self.on_change = on_change
        
        self.rect = None
        self.hovered = False
    
    def toggle(self) -> None:
        """Toggle the state."""
        self.enabled = not self.enabled
        if self.on_change:
            self.on_change(self.enabled)


class SettingsMenu:
    """
    In-game settings menu.
    Allows adjustment of volume, graphics, etc.
    """
    
    def __init__(self, width: int = 400, height: int = 500):
        self.width = width
        self.height = height
        
        # Audio settings
        self.volume_music = Slider("Music Volume", 0, 1, MUSIC_VOLUME)
        self.volume_sfx = Slider("SFX Volume", 0, 1, SFX_VOLUME)
        self.volume_ambient = Slider("Ambient Volume", 0, 1, 0.5)
        
        # Graphics settings
        self.fullscreen = Toggle("Fullscreen", False)
        self.vsync = Toggle("VSync", True)
        self.show_particles = Toggle("Particles", True)
        self.screen_shake = Toggle("Screen Shake", True)
        
        # Gameplay settings
        self.difficulty = "normal"  # easy, normal, hard
        self.auto_save = Toggle("Auto-Save", True)
        self.debug_mode = Toggle("Debug Mode", False)
        
        # UI state
        self.open = False
        self.selected_item = 0
        self.items: List = [
            ("Audio Settings", None),
            self.volume_music,
            self.volume_sfx,
            self.volume_ambient,
            ("Graphics Settings", None),
            self.fullscreen,
            self.vsync,
            self.show_particles,
            self.screen_shake,
            ("Gameplay Settings", None),
            self.auto_save,
            ("Back", None),
        ]
    
    def toggle_open(self) -> None:
        """Open/close the settings menu."""
        self.open = not self.open
    
    def handle_input(self, key: int, mouse_pos: tuple = None) -> bool:
        """
        Handle input. Return True if input was consumed.
        """
        if not self.open:
            return False
        
        # Navigation
        if key == pygame.K_UP:
            self.selected_item = (self.selected_item - 1) % len(self.items)
            return True
        elif key == pygame.K_DOWN:
            self.selected_item = (self.selected_item + 1) % len(self.items)
            return True
        elif key == pygame.K_LEFT:
            item = self.items[self.selected_item]
            if isinstance(item, Slider):
                item.set_value(item.current_val - (item.max_val - item.min_val) * 0.05)
                # Update actual volume
                from audio.audio_manager import get_audio_manager
                am = get_audio_manager()
                if item == self.volume_music: am.music_manager.set_volume(item.current_val)
                elif item == self.volume_sfx: am.sfx_manager.set_volume(item.current_val)
                return True
        elif key == pygame.K_RIGHT:
            item = self.items[self.selected_item]
            if isinstance(item, Slider):
                item.set_value(item.current_val + (item.max_val - item.min_val) * 0.05)
                # Update actual volume
                from audio.audio_manager import get_audio_manager
                am = get_audio_manager()
                if item == self.volume_music: am.music_manager.set_volume(item.current_val)
                elif item == self.volume_sfx: am.sfx_manager.set_volume(item.current_val)
                return True
        elif key == pygame.K_RETURN or key == pygame.K_SPACE:
            item = self.items[self.selected_item]
            if isinstance(item, Toggle):
                item.toggle()
                # Handle specific toggles
                if item == self.fullscreen:
                    pygame.display.toggle_fullscreen()
                return True
            elif isinstance(item, tuple) and item[0] == "Back":
                self.toggle_open()
                return True
        elif key == pygame.K_ESCAPE:
            self.toggle_open()
            return True
        
        return False
    
    def render(self, surface: pygame.Surface) -> None:
        """Render the settings menu."""
        if not self.open:
            return
        
        # Draw semi-transparent overlay
        overlay = pygame.Surface(surface.get_size())
        overlay.fill((0, 0, 0))
        overlay.set_alpha(200)
        surface.blit(overlay, (0, 0))
        
        # Draw menu background
        menu_x = (surface.get_width() - self.width) // 2
        menu_y = (surface.get_height() - self.height) // 2
        menu_rect = pygame.Rect(menu_x, menu_y, self.width, self.height)
        
        pygame.draw.rect(surface, (40, 40, 50), menu_rect)
        pygame.draw.rect(surface, (100, 100, 150), menu_rect, 2)
        
        # Draw title
        title_font = pygame.font.SysFont(None, 32)
        title_text = title_font.render("Settings", True, (200, 200, 220))
        surface.blit(title_text, (menu_x + 20, menu_y + 20))
        
        # Draw menu items
        item_font = pygame.font.SysFont(None, 24)
        y = menu_y + 80
        item_height = 40
        
        for i, item in enumerate(self.items):
            is_selected = i == self.selected_item
            color = (255, 255, 100) if is_selected else (200, 200, 200)
            
            if isinstance(item, tuple):
                # Section header
                text_surface = item_font.render(item[0], True, (150, 150, 200))
                surface.blit(text_surface, (menu_x + 30, y))
            elif isinstance(item, Slider):
                # Slider
                self._render_slider(surface, item, menu_x + 30, y, is_selected)
            elif isinstance(item, Toggle):
                # Toggle
                checkbox = "✓" if item.enabled else "○"
                text = f"{checkbox} {item.label}"
                text_surface = item_font.render(text, True, color)
                surface.blit(text_surface, (menu_x + 30, y))
            
            y += item_height
    
    def _render_slider(self, surface: pygame.Surface, slider: Slider, x: int, y: int,
                      is_selected: bool) -> None:
        """Render a slider control."""
        font = pygame.font.SysFont(None, 20)
        
        # Label and value
        label_color = (255, 255, 100) if is_selected else (200, 200, 200)
        label_text = font.render(f"{slider.label}: {int(slider.current_val * 100)}%", 
                                True, label_color)
        surface.blit(label_text, (x, y))
        
        # Slider bar
        bar_width = 250
        bar_height = 10
        bar_rect = pygame.Rect(x, y + 25, bar_width, bar_height)
        pygame.draw.rect(surface, (60, 60, 70), bar_rect)
        pygame.draw.rect(surface, (100, 100, 120), bar_rect, 1)
        
        # Slider thumb
        thumb_x = x + bar_width * slider.get_normalized()
        pygame.draw.circle(surface, (150, 150, 200), (int(thumb_x), y + 30), 6)


# Global settings instance
_settings_menu: Optional[SettingsMenu] = None

def get_settings_menu() -> SettingsMenu:
    """Get or create global settings menu."""
    global _settings_menu
    if _settings_menu is None:
        _settings_menu = SettingsMenu()
    return _settings_menu
