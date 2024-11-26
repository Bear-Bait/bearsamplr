#!/usr/bin/env python3

import os
import time
import numpy as np
import sounddevice as sd
import RPi.GPIO as GPIO
import subprocess

class AudioDiagnostics:
    def __init__(self):
        self.sample_rate = 44100
        self.success = True
        
    def print_result(self, test_name, result, message=""):
        """Print test result in a consistent format"""
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: [{status}] {message}")
        if not result:
            self.success = False
        print("-" * 50)
        
    def test_gpio_dac(self):
        """Test GPIO configuration for DAC"""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(25, GPIO.OUT)
            initial_state = GPIO.input(25)
            
            # Toggle GPIO
            GPIO.output(25, GPIO.HIGH)
            high_state = GPIO.input(25)
            GPIO.output(25, GPIO.LOW)
            low_state = GPIO.input(25)
            GPIO.output(25, GPIO.HIGH)  # Return to high for normal operation
            
            result = high_state == 1 and low_state == 0
            self.print_result("GPIO DAC Control", result, 
                            f"Initial state: {initial_state}, Can toggle: {result}")
            return result
        except Exception as e:
            self.print_result("GPIO DAC Control", False, f"Error: {str(e)}")
            return False
            
    def test_audio_devices(self):
        """Check available audio devices"""
        try:
            devices = sd.query_devices()
            print("\nAvailable Audio Devices:")
            print("------------------------")
            for i, device in enumerate(devices):
                print(f"[{i}] {device['name']}")
                print(f"    Channels: {device['max_input_channels']}in, {device['max_output_channels']}out")
                print(f"    Sample Rates: {device['default_samplerate']}")
            
            # Check specifically for HiFiBerry
            hifiberry_found = any('HiFiBerry' in d['name'] for d in devices)
            self.print_result("Audio Device Detection", True, 
                            "HiFiBerry DAC " + ("found" if hifiberry_found else "not found"))
            return True
        except Exception as e:
            self.print_result("Audio Device Detection", False, f"Error: {str(e)}")
            return False
            
    def test_alsa_config(self):
        """Check ALSA configuration"""
        try:
            print("\nALSA Configuration:")
            print("-----------------")
            # Check aplay devices
            aplay_output = subprocess.check_output(['aplay', '-l'], text=True)
            print(aplay_output)
            
            # Check current ALSA config
            if os.path.exists('/etc/asound.conf'):
                with open('/etc/asound.conf', 'r') as f:
                    print("asound.conf contents:")
                    print(f.read())
            else:
                print("No /etc/asound.conf found")
                
            hifiberry_found = 'HiFiBerry' in aplay_output
            self.print_result("ALSA Configuration", hifiberry_found, 
                            "HiFiBerry " + ("found" if hifiberry_found else "not found") + " in ALSA devices")
            return hifiberry_found
        except Exception as e:
            self.print_result("ALSA Configuration", False, f"Error: {str(e)}")
            return False
            
    def test_sine_wave(self):
        """Test basic audio output with sine wave"""
        try:
            print("\nTesting audio output with sine wave...")
            print("You should hear a 440Hz tone for 2 seconds")
            
            # Generate test tone
            duration = 2
            frequency = 440
            t = np.linspace(0, duration, int(self.sample_rate * duration), False)
            test_tone = 0.5 * np.sin(2 * np.pi * frequency * t)
            
            # Try to play the tone
            sd.play(test_tone, self.sample_rate)
            sd.wait()
            
            # Ask for user confirmation
            response = input("Did you hear the tone? (y/n): ").lower().strip()
            result = response == 'y'
            self.print_result("Sine Wave Test", result, 
                            "Audio " + ("working" if result else "not working"))
            return result
        except Exception as e:
            self.print_result("Sine Wave Test", False, f"Error: {str(e)}")
            return False
            
    def test_audio_permissions(self):
        """Check audio-related permissions"""
        try:
            print("\nChecking audio permissions:")
            # Check audio group
            groups_output = subprocess.check_output(['groups'], text=True)
            audio_group_ok = 'audio' in groups_output
            print(f"User groups: {groups_output.strip()}")
            
            # Check device permissions
            ls_output = subprocess.check_output(['ls', '-l', '/dev/snd'], text=True)
            print("\nAudio device permissions:")
            print(ls_output)
            
            self.print_result("Audio Permissions", audio_group_ok, 
                            "User " + ("has" if audio_group_ok else "does not have") + " audio group permissions")
            return audio_group_ok
        except Exception as e:
            self.print_result("Audio Permissions", False, f"Error: {str(e)}")
            return False
            
    def run_all_tests(self):
        """Run all diagnostic tests"""
        try:
            print("\nStarting BearSampler Audio Diagnostics")
            print("====================================")
            
            self.test_gpio_dac()
            self.test_audio_devices()
            self.test_alsa_config()
            self.test_audio_permissions()
            self.test_sine_wave()
            
            print("\nDiagnostic Summary")
            print("=================")
            print(f"Overall Status: {'PASS' if self.success else 'FAIL'}")
            
        except Exception as e:
            print(f"\nDiagnostic error: {e}")
        finally:
            GPIO.cleanup()

if __name__ == "__main__":
    try:
        diagnostics = AudioDiagnostics()
        diagnostics.run_all_tests()
    except KeyboardInterrupt:
        print("\nDiagnostics interrupted by user")
    except Exception as e:
        print(f"\nFatal error: {e}")
    finally:
        GPIO.cleanup()
