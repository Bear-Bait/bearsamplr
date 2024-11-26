#!/usr/bin/env python3

import pygame
import time
import os

def test_audio():
    """Test audio output through HiFiBerry DAC"""
    try:
        # Initialize pygame with specific settings for HiFiBerry
        pygame.mixer.pre_init(
            frequency=44100,
            size=-16,
            channels=2,
            buffer=2048,
            devicename="plughw:0,0"  # Use HiFiBerry DAC (card 0, device 0)
        )
        pygame.init()
        pygame.mixer.init()
        
        # Set volume
        pygame.mixer.music.set_volume(0.5)
        
        # Use speaker-test to generate a test tone
        print("Playing test tone...")
        os.system("speaker-test -t sine -f 440 -c 2 -D plughw:0,0 -l 1 >/dev/null 2>&1")
        
        # Small delay
        time.sleep(2)
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        pygame.mixer.quit()
        pygame.quit()

if __name__ == "__main__":
    print("Testing HiFiBerry DAC audio output...")
    if test_audio():
        print("Audio test completed. Did you hear a tone? (y/n)")
        response = input().lower()
        if response == 'y':
            print("Audio is working!")
        else:
            print("Audio test failed - no sound heard")
    else:
        print("Audio test failed - error during playback")
