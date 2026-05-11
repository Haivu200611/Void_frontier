"""
Sprite rendering system.
Handles sprite loading, scaling, flipping, and rendering.
"""

import pygame
import os
from typing import Dict, Tuple, Optional


class SpriteRenderer:
    """
    Manages sprite loading and rendering.
    Supports:
    - Sprite scaling
    - Sprite flipping (h/v)
    - Cached sprite loading
    - Layered rendering
    - Color tinting
    """

    def __init__(self):
        self.sprite_cache: Dict[str, pygame.Surface] = {}
        self.sprite_dir = "assets/images"
        
    def load_sprite(self, key: str, path: str = None, width: int = None, height: int = None) -> Optional[pygame.Surface]:
        """
        Load a sprite from file and store it with a key.
        
        :param key: Unique identifier for the sprite
        :param path: Optional relative path from assets/images
        :param width: Optional width to scale to
        :param height: Optional height to scale to
        :return: Pygame surface or None if file doesn't exist
        """
        # Check cache first
        if key in self.sprite_cache:
            return self.sprite_cache[key]
            
        if not path:
            # If no path provided and not in cache, try using key as path
            path = key
            
        full_path = os.path.join(self.sprite_dir, path) if not os.path.isabs(path) else path
        
        # Try to load file
        if not os.path.exists(full_path):
            # Return placeholder surface instead of failing
            placeholder = self._create_placeholder(width or 64, height or 64)
            self.sprite_cache[key] = placeholder
            return placeholder
        
        try:
            sprite = pygame.image.load(full_path).convert_alpha()
            
            # Scale if needed
            if width or height:
                w = width or sprite.get_width()
                h = height or sprite.get_height()
                sprite = pygame.transform.scale(sprite, (int(w), int(h)))
            
            self.sprite_cache[key] = sprite
            return sprite
        except Exception as e:
            print(f"Failed to load sprite {full_path}: {e}")
            placeholder = self._create_placeholder(width or 64, height or 64)
            self.sprite_cache[key] = placeholder
            return placeholder
    
    def _create_placeholder(self, width: int, height: int) -> pygame.Surface:
        """Create a placeholder surface with a checkerboard pattern."""
        surface = pygame.Surface((int(width), int(height)))
        surface.fill((50, 50, 50))
        
        # Checkerboard pattern
        sq_size = 8
        for x in range(0, int(width), sq_size * 2):
            for y in range(0, int(height), sq_size * 2):
                pygame.draw.rect(surface, (80, 80, 80), (x, y, sq_size, sq_size))
                pygame.draw.rect(surface, (80, 80, 80), (x + sq_size, y + sq_size, sq_size, sq_size))
        
        pygame.draw.rect(surface, (100, 100, 100), (0, 0, int(width), int(height)), 1)
        surface.set_colorkey((0, 0, 0))
        return surface
    
    def flip_sprite(self, sprite: pygame.Surface, horizontal: bool = False, 
                   vertical: bool = False) -> pygame.Surface:
        """Flip a sprite horizontally and/or vertically."""
        if horizontal or vertical:
            sprite = pygame.transform.flip(sprite, horizontal, vertical)
        return sprite
    
    def scale_sprite(self, sprite: pygame.Surface, width: int, height: int) -> pygame.Surface:
        """Scale a sprite to new dimensions."""
        return pygame.transform.scale(sprite, (int(width), int(height)))
    
    def tint_sprite(self, sprite: pygame.Surface, color: Tuple[int, int, int], 
                   alpha: float = 1.0) -> pygame.Surface:
        """Tint a sprite with a color overlay."""
        tinted = sprite.copy()
        tinted.fill((*color, int(alpha * 255)), special_flags=pygame.BLEND_MULT)
        return tinted
    
    def render_sprite(self, surface: pygame.Surface, sprite_input: any,
                     x: float, y: float, offset_x: float = 0, offset_y: float = 0,
                     scale: float = 1.0, flip_x: bool = False, flip_y: bool = False,
                     alpha: int = 255, rotation: float = 0, tint: Tuple[int, int, int] = None) -> None:
        """
        Render a sprite to screen.
        
        :param surface: Target pygame surface
        :param sprite_input: Sprite surface or key name
        :param x: World X position
        :param y: World Y position
        :param offset_x: Camera X offset
        :param offset_y: Camera Y offset
        :param scale: Scale factor
        :param flip_x: Flip horizontally
        :param flip_y: Flip vertically
        :param alpha: Opacity (0-255)
        :param rotation: Rotation in degrees
        :param tint: Color tint tuple (R, G, B)
        """
        sprite = sprite_input
        if isinstance(sprite_input, str):
            sprite = self.load_sprite(sprite_input)
            
        if sprite is None:
            return
        
        # Apply transforms
        rendered = sprite.copy()
        
        if tint:
            rendered = self.tint_sprite(rendered, tint)
        
        if scale != 1.0:
            w = int(sprite.get_width() * scale)
            h = int(sprite.get_height() * scale)
            rendered = pygame.transform.scale(rendered, (w, h))
        
        if flip_x or flip_y:
            rendered = pygame.transform.flip(rendered, flip_x, flip_y)
        
        if rotation != 0:
            rendered = pygame.transform.rotate(rendered, rotation)
        
        if alpha < 255:
            rendered.set_alpha(alpha)
        
        # Screen position (apply camera offset)
        screen_x = int(x - offset_x)
        screen_y = int(y - offset_y)
        
        # Blit to surface
        rect = rendered.get_rect(center=(screen_x, screen_y))
        surface.blit(rendered, rect)
    
    def clear_cache(self):
        """Clear sprite cache to free memory."""
        self.sprite_cache.clear()


# Global sprite renderer instance
_sprite_renderer: Optional[SpriteRenderer] = None

def get_sprite_renderer() -> SpriteRenderer:
    """Get or create the global sprite renderer."""
    global _sprite_renderer
    if _sprite_renderer is None:
        _sprite_renderer = SpriteRenderer()
    return _sprite_renderer
