import pygame
from settings import WINDOW_WIDTH, WINDOW_HEIGHT

class Spaceship:
    def __init__(self, x: float, y: float):
        self.x = float(x)
        self.y = float(y)
        
        # Load and scale spaceship image (3x the player size => player is 48px, ship is 144px)
        try:
            image = pygame.image.load("assets/images/spaceship/spaceship.png").convert_alpha()
            self.image = pygame.transform.smoothscale(image, (144, 144))
        except Exception as e:
            print(f"Failed to load spaceship image: {e}")
            # Fallback
            self.image = pygame.Surface((144, 144), pygame.SRCALPHA)
            pygame.draw.rect(self.image, (100, 100, 120), (0, 0, 144, 144))
            pygame.draw.circle(self.image, (50, 200, 250), (72, 72), 30)

        # Rect for collision (impassable)
        self.rect = pygame.Rect(0, 0, 144, 144)
        self.rect.center = (int(self.x), int(self.y))
        
    def render(self, surface: pygame.Surface, offset_x: float, offset_y: float) -> None:
        screen_x = int(self.x - offset_x)
        screen_y = int(self.y - offset_y)
        
        # Frustum culling check
        screen_width, screen_height = surface.get_size()
        if (screen_x + 72 < 0 or screen_x - 72 > screen_width or
            screen_y + 72 < 0 or screen_y - 72 > screen_height):
            return
            
        surface.blit(self.image, (screen_x - 72, screen_y - 72))
