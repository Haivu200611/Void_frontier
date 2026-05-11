"""
UI-specific audio manager.
"""

from audio.audio_manager import AudioManager


class UIAudioManager:
    """Manages UI and menu sounds."""
    
    def __init__(self, audio_manager: AudioManager):
        self.audio = audio_manager
    
    def play_button_click(self) -> None:
        """Play button click sound."""
        self.audio.play_ui_sound("button_click.wav", 0.8)
    
    def play_button_hover(self) -> None:
        """Play button hover sound."""
        self.audio.play_ui_sound("button_hover.wav", 0.6)
    
    def play_menu_open(self) -> None:
        """Play menu open sound."""
        self.audio.play_ui_sound("menu_open.wav")
    
    def play_menu_close(self) -> None:
        """Play menu close sound."""
        self.audio.play_ui_sound("menu_close.wav")
    
    def play_notification(self) -> None:
        """Play notification sound."""
        self.audio.play_ui_sound("notification.wav", 0.7)
    
    def play_level_up(self) -> None:
        """Play level up sound."""
        self.audio.play_ui_sound("levelup.wav")
    
    def play_equip(self) -> None:
        """Play item equip sound."""
        self.audio.play_ui_sound("equip.wav", 0.8)
    
    def play_pick_up(self) -> None:
        """Play item pickup sound."""
        self.audio.play_ui_sound("pickup.wav", 0.7)
