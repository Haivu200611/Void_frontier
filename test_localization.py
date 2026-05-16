"""
Test script for localization system
"""
import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from systems.localization import get_localization_manager, _

def test_localization():
    """Test localization system"""
    print("=" * 50)
    print("LOCALIZATION SYSTEM TEST")
    print("=" * 50)
    
    # Get manager
    loc_manager = get_localization_manager()
    
    print(f"\nCurrent Language: {loc_manager.get_language()}")
    print(f"Available Languages: {loc_manager.available_languages}")
    
    # Test English translations
    print("\n--- ENGLISH TRANSLATIONS ---")
    loc_manager.set_language("en")
    print(f"Language: {loc_manager.get_language_name(loc_manager.get_language())}")
    print(f"menu.play = {_('menu.play')}")
    print(f"menu.how_to_play = {_('menu.how_to_play')}")
    print(f"menu.language = {_('menu.language')}")
    print(f"menu.quit = {_('menu.quit')}")
    print(f"hud.health = {_('hud.health')}")
    print(f"hud.oxygen = {_('hud.oxygen')}")
    
    # Test Vietnamese translations
    print("\n--- VIETNAMESE TRANSLATIONS ---")
    loc_manager.set_language("vi")
    print(f"Language: {loc_manager.get_language_name(loc_manager.get_language())}")
    print(f"menu.play = {_('menu.play')}")
    print(f"menu.how_to_play = {_('menu.how_to_play')}")
    print(f"menu.language = {_('menu.language')}")
    print(f"menu.quit = {_('menu.quit')}")
    print(f"hud.health = {_('hud.health')}")
    print(f"hud.oxygen = {_('hud.oxygen')}")
    
    # Test language switching
    print("\n--- LANGUAGE SWITCHING TEST ---")
    print(f"Starting language: {loc_manager.get_language()}")
    print(f"'menu.play' = {_('menu.play')}")
    
    print("\nSwitching to English...")
    loc_manager.set_language("en")
    print(f"Current language: {loc_manager.get_language()}")
    print(f"'menu.play' = {_('menu.play')}")
    
    print("\nSwitching to Vietnamese...")
    loc_manager.set_language("vi")
    print(f"Current language: {loc_manager.get_language()}")
    print(f"'menu.play' = {_('menu.play')}")
    
    # Test default value
    print("\n--- DEFAULT VALUE TEST ---")
    missing_key = _('nonexistent.key', 'DEFAULT VALUE')
    print(f"Missing key returns: '{missing_key}'")
    
    print("\n" + "=" * 50)
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 50)

if __name__ == "__main__":
    test_localization()
