#!/usr/bin/env python3

import time
import pygame
import RPi.GPIO as GPIO
import numpy as np
import wave
import struct

def setup_dac():
    """Configure GPIO for the PCM5102A DAC"""
    try:
        GPIO.setmode(GPIO.BCM)
        # Set GPIO 25 high to enable the DAC
        GPIO.setup(25, GPIO.OUT)
        GPIO.output(25, GPIO.HIGH)
        return True
    except Exception as e:
        print(f"DAC setup error: {e}")
        return False

def generate_test_tone():
    """Generate a test tone WAV file"""
    # Audio parameters
    sample_rate = 44100
    duration = 2  # seconds
    frequency = 440  # Hz (A4 note)
    amplitude = 0.5  # 50% volume
    
    # Generate samples
    samples = amplitude * np.sin(2.0 * np.pi * frequency * np.linspace(0, duration, int(duration * sample_rate)))
    
    # Convert to 16-bit integers
    samples = (samples * 32767).astype(np.int16)
    
    # Write WAV file
    with wave.open('test_tone.wav', 'w') as wav_file:
        # Set parameters
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes per sample
        wav_file.setframerate(sample_rate)
        
        # Write data
        wav_file.writeframes(samples.tobytes())

def test_audio():
    """Run audio test sequence"""
    try:
        print("Setting up DAC...")
        if not setup_dac():
            return False
        
        print("\nInitializing pygame audio...")
        pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=2048)
        
        print("\nGenerating test tone...")
        generate_test_tone()
        
        print("\nLoading and playing test tone...")
        print("You should hear a 440 Hz tone (A4 note)")
        
        pygame.mixer.music.load('test_tone.wav')
        pygame.mixer.music.set_volume(0.5)  # 50% volume
        pygame.mixer.music.play()
        
        # Wait for the sound to finish
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        
        print("\nTest completed successfully")
        return True
        
    except Exception as e:
        print(f"\nError during audio test: {e}")
        return False
    finally:
        pygame.mixer.quit()
        GPIO.cleanup()

if __name__ == "__main__":
    try:
        print("Starting audio test...")
        print("Make sure your headphones are connected and volume is at a moderate level")
        input("Press Enter to begin test (Ctrl+C to cancel)...")
        
        test_audio()
        
    except KeyboardInterrupt:
        print("\nTest cancelled by user")
    finally:
        pygame.mixer.quit()
        GPIO.cleanup()#!/usr/bin/env python3

import time
import pygame
import RPi.GPIO as GPIO
import numpy as np
import wave
import struct

def setup_dac():
    """Configure GPIO for the PCM5102A DAC"""
    try:
        GPIO.setmode(GPIO.BCM)
        # Set GPIO 25 high to enable the DAC
        GPIO.setup(25, GPIO.OUT)
        GPIO.output(25, GPIO.HIGH)
        return True
    except Exception as e:
        print(f"DAC setup error: {e}")
        return False

def generate_test_tone():
    """Generate a test tone WAV file"""
    # Audio parameters
    sample_rate = 44100
    duration = 2  # seconds
    frequency = 440  # Hz (A4 note)
    amplitude = 0.5  # 50% volume
    
    # Generate samples
    samples = amplitude * np.sin(2.0 * np.pi * frequency * np.linspace(0, duration, int(duration * sample_rate)))
    
    # Convert to 16-bit integers
    samples = (samples * 32767).astype(np.int16)
    
    # Write WAV file
    with wave.open('test_tone.wav', 'w') as wav_file:
        # Set parameters
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes per sample
        wav_file.setframerate(sample_rate)
        
        # Write data
        wav_file.writeframes(samples.tobytes())

def test_audio():
    """Run audio test sequence"""
    try:
        print("Setting up DAC...")
        if not setup_dac():
            return False
        
        print("\nInitializing pygame audio...")
        pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=2048)
        
        print("\nGenerating test tone...")
        generate_test_tone()
        
        print("\nLoading and playing test tone...")
        print("You should hear a 440 Hz tone (A4 note)")
        
        pygame.mixer.music.load('test_tone.wav')
        pygame.mixer.music.set_volume(0.5)  # 50% volume
        pygame.mixer.music.play()
        
        # Wait for the sound to finish
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        
        print("\nTest completed successfully")
        return True
        
    except Exception as e:
        print(f"\nError during audio test: {e}")
        return False
    finally:
        pygame.mixer.quit()
        GPIO.cleanup()

if __name__ == "__main__":
    try:
        print("Starting audio test...")
        print("Make sure your headphones are connected and volume is at a moderate level")
        input("Press Enter to begin test (Ctrl+C to cancel)...")
        
        test_audio()
        
    except KeyboardInterrupt:
        print("\nTest cancelled by user")
    finally:
        pygame.mixer.quit()
        GPIO.cleanup()
