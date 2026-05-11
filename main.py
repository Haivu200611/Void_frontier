import pygame
import sys
import os
from settings import *
from core.engine import GameEngine

def main():
    # Change working directory to the directory of this script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    pygame.init()
    engine = GameEngine()
    engine.run()
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()