import os
import tempfile
import cv2
import pygame
import numpy as np

from core.state_machine import State
from settings import *
from audio.audio_manager import get_audio_manager


class OuttroState(State):
    """Plays outtro video at the end of the game."""
    
    def enter(self, **kwargs):
        self.video_path = "assets/images/intro_outtro/outtro.mp4"
        self.audio_manager = get_audio_manager()
        self.audio_manager.stop_music(fade_out=0.5)
        self.cap = None
        self.current_frame = None
        self.fps = 30
        self.frame_count = 0
        self.total_frames = 0
        self.video_duration = 0  # in seconds
        self.elapsed_time = 0
        self.finished = False
        self.skip_pressed = False
        self._temp_audio_path = None
        
        # Try to open the video
        if os.path.exists(self.video_path):
            self.cap = cv2.VideoCapture(self.video_path)
            if self.cap.isOpened():
                self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
                self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
                self.video_duration = self.total_frames / self.fps if self.fps > 0 else 0
                
                # Extract and play audio from video
                self._start_video_audio()
            else:
                print(f"Failed to open video: {self.video_path}")
                self.finished = True
        else:
            print(f"Video file not found: {self.video_path}")
            self.finished = True
    
    def _start_video_audio(self):
        """Extract audio from video and play it via pygame.mixer.music."""
        try:
            from moviepy import VideoFileClip
            
            clip = VideoFileClip(self.video_path)
            if clip.audio is not None:
                # Write audio to a temp WAV file
                temp_dir = os.path.join(os.path.dirname(self.video_path), "..")
                self._temp_audio_path = os.path.join(
                    tempfile.gettempdir(), "vf_outtro_audio.wav"
                )
                clip.audio.write_audiofile(
                    self._temp_audio_path,
                    logger=None  # Suppress progress bar
                )
                clip.close()
                
                # Play the extracted audio
                pygame.mixer.music.load(self._temp_audio_path)
                pygame.mixer.music.set_volume(0.8)
                pygame.mixer.music.play()
            else:
                clip.close()
                print("Video has no audio track")
        except ImportError:
            print("moviepy not installed - video will play without audio")
        except Exception as e:
            print(f"Failed to extract video audio: {e}")
    
    def handle_events(self, events):
        """Handle input events - allow skipping outtro with any key/click."""
        for event in events:
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                self.skip_pressed = True
    
    def update(self, dt):
        """Update video playback."""
        if self.finished:
            return
        
        if self.skip_pressed:
            self.finished = True
            self.transition_to_ending()
            return
        
        self.elapsed_time += dt
        
        # Check if video has finished
        if self.elapsed_time >= self.video_duration:
            self.finished = True
            self.transition_to_ending()
            return
        
        # Calculate which frame we should be at
        target_frame = int(self.elapsed_time * self.fps)
        
        # Read frames until we reach the target frame
        if self.cap and self.cap.isOpened():
            while self.frame_count < target_frame and self.frame_count < self.total_frames:
                ret, frame = self.cap.read()
                if ret:
                    self.current_frame = frame
                    self.frame_count += 1
                else:
                    self.finished = True
                    self.transition_to_ending()
                    return
    
    def transition_to_ending(self):
        """Transition to the ending state."""
        # Stop video audio
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        
        if self.cap:
            self.cap.release()
        
        # Clean up temp audio file
        self._cleanup_temp_audio()
        
        self.engine.state_machine.change_state("Ending")
    
    def render(self, surface):
        """Render the current video frame."""
        # Fill background with black
        surface.fill((0, 0, 0))
        
        if self.current_frame is not None:
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)
            
            # Resize frame to fit window while maintaining aspect ratio
            h, w = frame_rgb.shape[:2]
            aspect_ratio = w / h
            window_aspect = WINDOW_WIDTH / WINDOW_HEIGHT
            
            if aspect_ratio > window_aspect:
                # Width is the constraint
                new_w = WINDOW_WIDTH
                new_h = int(WINDOW_WIDTH / aspect_ratio)
            else:
                # Height is the constraint
                new_h = WINDOW_HEIGHT
                new_w = int(WINDOW_HEIGHT * aspect_ratio)
            
            frame_rgb = cv2.resize(frame_rgb, (new_w, new_h))
            
            # Convert to pygame surface
            frame_surface = pygame.image.fromstring(
                frame_rgb.tobytes(),
                (new_w, new_h),
                'RGB'
            )
            
            # Center on screen
            x = (WINDOW_WIDTH - new_w) // 2
            y = (WINDOW_HEIGHT - new_h) // 2
            surface.blit(frame_surface, (x, y))
        
        # Optional: Display skip hint
        if self.elapsed_time < 2.0:  # Show hint for first 2 seconds
            font = pygame.font.SysFont("segoeui", 16)
            hint = font.render("Press any key or click to skip", True, (200, 200, 200))
            hint_rect = hint.get_rect(bottomright=(WINDOW_WIDTH - 20, WINDOW_HEIGHT - 20))
            surface.blit(hint, hint_rect)
    
    def exit(self):
        """Clean up resources when exiting state."""
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        
        if self.cap:
            self.cap.release()
        
        self._cleanup_temp_audio()
    
    def _cleanup_temp_audio(self):
        """Remove temporary audio file if it exists."""
        if self._temp_audio_path and os.path.exists(self._temp_audio_path):
            try:
                # Unload from mixer first
                try:
                    pygame.mixer.music.unload()
                except Exception:
                    pass
                os.remove(self._temp_audio_path)
            except Exception:
                pass
            self._temp_audio_path = None
