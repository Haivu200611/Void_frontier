"""
Sprite batching system for optimized rendering.
Combines multiple sprites into a single draw call where possible.
"""

import pygame
from typing import List, Tuple, Optional

class SpriteBatch:
    """
    Batches sprite draw calls to improve performance.
    Useful for many small sprites with same texture or layer.
    """
    
    def __init__(self):
        self.batch: List[Tuple[pygame.Surface, pygame.Rect, Optional[int]]] = []
        self.active = False
        
    def begin(self):
        """Start batching."""
        self.batch.clear()
        self.active = True
        
    def draw(self, surface: pygame.Surface, rect: pygame.Rect, alpha: Optional[int] = None):
        """Add a sprite to the current batch."""
        if not self.active:
            print("Warning: Attempted to draw without beginning batch.")
            return
        self.batch.append((surface, rect, alpha))
        
    def end(self, target_surface: pygame.Surface):
        """Render the batch to the target surface and end batching."""
        if not self.active:
            return
            
        for surface, rect, alpha in self.batch:
            if alpha is not None and alpha < 255:
                surface.set_alpha(alpha)
            target_surface.blit(surface, rect)
            
        self.active = False
        self.batch.clear()

# Global batch instance
_sprite_batch: Optional[SpriteBatch] = None

def get_sprite_batch() -> SpriteBatch:
    """Get or create the global sprite batch."""
    global _sprite_batch
    if _sprite_batch is None:
        _sprite_batch = SpriteBatch()
    return _sprite_batch
