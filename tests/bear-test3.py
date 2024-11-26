#!/usr/bin/env python3

import os
import math
import random
import pygame
import st7789
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from time import sleep, time
import sounddevice as sd
import numpy as np
import rtmidi
from pathlib import Path
import logging
from datetime import datetime
import threading
import configparser
import re

# Initialize logging
log_filename = f"bearsampler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Global state
class GlobalState:
    def __init__(self):
        self.PRESET = 0
        self.samples = {}
        self.playingsounds = []
        self.playingnotes = {}
        self.sustainplayingnotes = []
        self.triggernotes = [128]*128
        self.currvoice = 0
        self.volume = 0.8
        self.midi_mute = False
        self.stopping = False
        self.ActuallyLoading = False
        self.presetlist = []
        self.voicelist = []
        self.basename = None
        self.currbase = None
        self.LoadingSamples = None
        
gv = GlobalState()


# GPIO Management
class GPIOManager:
    def __init__(self, button_config):
        self.buttons = button_config
        self.initialized = False
        
    def initialize(self):
        """Initialize GPIO pins"""
        try:
            if not self.initialized:
                GPIO.setmode(GPIO.BCM)
                for button in self.buttons.values():
                    GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                self.initialized = True
                logging.info("GPIO initialized successfully")
                return True
        except Exception as e:
            logging.error(f"GPIO initialization error: {e}")
            return False
            
    def cleanup(self):
        """Clean up GPIO resources"""
        if self.initialized:
            try:
                GPIO.cleanup()
                self.initialized = False
                logging.info("GPIO cleaned up successfully")
            except Exception as e:
                logging.error(f"GPIO cleanup error: {e}")

# Sound class for sample management
class Sound:
    def __init__(self, filename, voice, midinote, velocity, mode="Keyb", release=30):
        self.filename = filename
        self.voice = voice
        self.midinote = midinote
        self.velocity = velocity
        self.mode = mode
        self.release = release
        self.data = None
        self.load()

    def load(self):
        try:
            audio_data, _ = sd.read(self.filename)
            if len(audio_data.shape) == 1:
                audio_data = np.column_stack((audio_data, audio_data))
            self.data = audio_data
            return True
        except Exception as e:
            logging.error(f"Error loading sample {self.filename}: {e}")
            return False

    def play(self, note, velocity):
        sound = PlayingSound(self, note, velocity)
        gv.playingsounds.append(sound)
        return sound

# PlayingSound class for active sound management
class PlayingSound:
    def __init__(self, sound, note, velocity):
        self.sound = sound
        self.pos = 0
        self.note = note
        self.velocity = velocity
        self.fadeout = False
        self.fadein = False

# Main BearSampler class
class BearSampler:
    def __init__(self):
        self.gpio_manager = GPIOManager(HARDWARE_CONFIG['BUTTONS'])
        self.display_manager = DisplayManager(HARDWARE_CONFIG)
        self.audio_engine = AudioEngine(HARDWARE_CONFIG)
        self.running = True
        
    def initialize(self):
        """Initialize all subsystems"""
        try:
            # Initialize GPIO first
            if not self.gpio_manager.initialize():
                raise RuntimeError("GPIO initialization failed")
            
            # Initialize display
            if not self.display_manager.initialize():
                raise RuntimeError("Display initialization failed")
            
            # Initialize audio
            if not self.audio_engine.initialize():
                raise RuntimeError("Audio initialization failed")
            
            return True
            
        except Exception as e:
            logging.error(f"Initialization error: {e}")
            return False
            
    def cleanup(self):
        """Clean up all resources"""
        logging.info("Cleaning up...")
        if hasattr(self, 'audio_engine'):
            self.audio_engine.cleanup()
        self.gpio_manager.cleanup()
        logging.info("Cleanup complete")

    def run(self):
        """Main program loop"""
        try:
            if not self.initialize():
                return
                
            logging.info("Starting main loop")
            while self.running:
                # Main loop code here
                sleep(0.1)
                
        except KeyboardInterrupt:
            logging.info("Received keyboard interrupt")
        except Exception as e:
            logging.error(f"Fatal error: {e}")
        finally:
            self.cleanup()

# Main program entry point
if __name__ == "__main__":
    try:
        sampler = BearSampler()
        sampler.run()
    except Exception as e:
        logging.error(f"Main program error: {e}")
        print(f"Fatal error: {e}")

# Constants
SAMPLES_DIR = "/media/usb/BearSampler"
FALLBACK_SAMPLES_DIR = os.path.expanduser("~/BearSampler")
CONFIG_DIR = "./config"

# Hardware Configuration
HARDWARE_CONFIG = {d     'DISPLAY': {
        'WIDTH': 240,
        'HEIGHT': 240,
        'ROTATION': 90,
        'SPI_SPEED_HZ': 80_000_000,
        'GPIO': {
            'DC': 9,
            'CS': 1,
            'BACKLIGHT': 13,
        }
    },
    'AUDIO': {
        'SAMPLE_RATE': 44100,
        'CHANNELS': 2,
        'BLOCKSIZE': 1024,
        'FORMAT': 'float32',
    },
    'BUTTONS': {
        'A': 5,
        'B': 6,
        'X': 16,
        'Y': 24
    }
}

# Sound class for sample management
class Sound:
    def __init__(self, filename, voice, midinote, velocity, mode="Keyb", release=30):
        self.filename = filename
        self.voice = voice
        self.midinote = midinote
        self.velocity = velocity
        self.mode = mode
        self.release = release
        self.data = None
        self.load()

    def load(self):
        try:
            audio_data, _ = sd.read(self.filename)
            if len(audio_data.shape) == 1:
                audio_data = np.column_stack((audio_data, audio_data))
            self.data = audio_data
            return True
        except Exception as e:
            logging.error(f"Error loading sample {self.filename}: {e}")
            return False

    def play(self, note, velocity):
        sound = PlayingSound(self, note, velocity)
        gv.playingsounds.append(sound)
        return sound

# PlayingSound class for active sound management
class PlayingSound:
    def __init__(self, sound, note, velocity):
        self.sound = sound
        self.pos = 0
        self.note = note
        self.velocity = velocity
        self.fadeout = False
        self.fadein = False

class SampleManager:
    def __init__(self):
        self.sample_path = Path(SAMPLES_DIR)
        self.fallback_path = Path(FALLBACK_SAMPLES_DIR)

    def load_preset(self, preset_number):
        try:
            preset_dir = self.sample_path / str(preset_number)
            if not preset_dir.exists():
                preset_dir = self.fallback_path / str(preset_number)
                if not preset_dir.exists():
                    logging.warning(f"Preset directory not found: {preset_number}")
                    return False

            # Clear existing samples
            gv.samples.clear()

            # Load all wav files in directory
            for sample_file in preset_dir.glob("*.wav"):
                try:
                    # Basic note extraction from filename
                    note = self.get_note_from_filename(sample_file.name)
                    if note is not None:
                        sound = Sound(str(sample_file), 1, note, 127)
                        if (note, 127, 1) in gv.samples:
                            gv.samples[note, 127, 1].append(sound)
                        else:
                            gv.samples[note, 127, 1] = [sound]
                except Exception as e:
                    logging.error(f"Error loading sample {sample_file}: {e}")

            return True

        except Exception as e:
            logging.error(f"Error loading preset {preset_number}: {e}")
            return False

    @staticmethod
    def get_note_from_filename(filename):
        """Extract MIDI note from filename"""
        try:
            note = int(filename.split('_')[1].split('.')[0])
            if 0 <= note <= 127:
                return note
        except:
            return None
        return None

# Continue with Display, MIDI, and Audio engine classes...

class DisplayManager:
    def __init__(self, config):
        self.width = config['DISPLAY']['WIDTH']
        self.height = config['DISPLAY']['HEIGHT']
        self.disp = st7789.ST7789(
            height=self.height,
            width=self.width,
            rotation=config['DISPLAY']['ROTATION'],
            port=0,
            cs=config['DISPLAY']['GPIO']['CS'],
            dc=config['DISPLAY']['GPIO']['DC'],
            backlight=config['DISPLAY']['GPIO']['BACKLIGHT'],
            spi_speed_hz=config['DISPLAY']['SPI_SPEED_HZ']
        )
        
        self.colors = {
            'background': (40, 0, 0),      # Deep crystal red
            'text': (255, 220, 220),       # Soft crystal white
            'accent': (255, 0, 0),         # Pure red
            'glow': (255, 40, 40),         # Red glow
            'shadow': (20, 0, 0),          # Deep shadow
            'crystal': (255, 180, 180)     # Crystal highlight
        }
        
        self.initialize()

    def initialize(self):
        """Initialize display and load fonts"""
        try:
            self.disp.begin()
            self.load_fonts()
            return True
        except Exception as e:
            logging.error(f"Display initialization error: {e}")
            return False

    def load_fonts(self):
        """Load system fonts or fall back to default"""
        try:
            self.font_large = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
            self.font_medium = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
            self.font_small = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        except:
            logging.warning("Could not load system fonts, using default")
            self.font_large = ImageFont.load_default()
            self.font_medium = ImageFont.load_default()
            self.font_small = ImageFont.load_default()

    def update_display(self, state):
        """Update display with current state"""
        image = Image.new('RGB', (self.width, self.height), self.colors['background'])
        draw = ImageDraw.Draw(image)

        # Draw preset information
        preset_text = f"Preset: {state.PRESET}"
        draw.text((20, 20), preset_text, 
                 font=self.font_medium, 
                 fill=self.colors['text'])

        # Draw playing notes count
        notes_text = f"Active Notes: {len(state.playingsounds)}"
        draw.text((20, 60), notes_text,
                 font=self.font_small,
                 fill=self.colors['text'])

        # Draw volume
        vol_text = f"Volume: {int(state.volume * 100)}%"
        draw.text((20, 100), vol_text,
                 font=self.font_small,
                 fill=self.colors['crystal'])

        self.disp.display(image)

    def show_loading(self, message):
        """Show loading screen"""
        image = Image.new('RGB', (self.width, self.height), self.colors['background'])
        draw = ImageDraw.Draw(image)
        
        draw.text((20, 110), "Loading...",
                 font=self.font_large,
                 fill=self.colors['crystal'])
        
        draw.text((20, 140), message,
                 font=self.font_small,
                 fill=self.colors['text'])
        
        self.disp.display(image)

    def show_error(self, error_message):
        """Show error screen"""
        image = Image.new('RGB', (self.width, self.height), self.colors['background'])
        draw = ImageDraw.Draw(image)
        
        draw.text((20, 100), "Error:",
                 font=self.font_large,
                 fill=self.colors['accent'])
        
        # Word wrap error message
        words = error_message.split()
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            test_line = ' '.join(current_line)
            bbox = draw.textbbox((0, 0), test_line, 
                               font=self.font_small)
            if bbox[2] - bbox[0] > 200:
                lines.append(' '.join(current_line[:-1]))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        
        y = 140
        for line in lines:
            draw.text((20, y), line,
                     font=self.font_small,
                     fill=self.colors['text'])
            y += 20
        
        self.disp.display(image) 

class AudioEngine:
    def __init__(self, config):
        self.sample_rate = config['AUDIO']['SAMPLE_RATE']
        self.channels = config['AUDIO']['CHANNELS']
        self.blocksize = config['AUDIO']['BLOCKSIZE']
        self.format = config['AUDIO']['FORMAT']
        self.stream = None
        self.volume = 0.8

    def initialize(self):
        """Initialize audio system"""
        try:
            sd.default.samplerate = self.sample_rate
            sd.default.channels = self.channels
            sd.default.blocksize = self.blocksize
            
            self.stream = sd.OutputStream(
                channels=self.channels,
                callback=self.audio_callback,
                samplerate=self.sample_rate,
                blocksize=self.blocksize
            )
            self.stream.start()
            logging.info("Audio engine initialized successfully")
            return True
        except Exception as e:
            logging.error(f"Audio initialization error: {e}")
            return False

    def audio_callback(self, outdata, frames, time, status):
        """Real-time audio callback"""
        if status:
            logging.warning(f"Audio callback status: {status}")
        
        try:
            # Initialize output buffer
            mixed = np.zeros((frames, self.channels), dtype=np.float32)
            
            # Mix all active sounds
            for sound in gv.playingsounds[:]:  # Copy list as we might modify it
                if sound.pos >= len(sound.sound.data):
                    gv.playingsounds.remove(sound)
                    continue
                
                # Calculate remaining samples
                available = len(sound.sound.data) - sound.pos
                n_samples = min(frames, available)
                
                # Apply volume and velocity scaling
                gain = (sound.velocity / 127.0) * self.volume
                
                # Mix into output buffer
                mixed[:n_samples] += sound.sound.data[sound.pos:sound.pos + n_samples] * gain
                
                # Update position
                sound.pos += n_samples

            # Prevent clipping
            mixed = np.clip(mixed, -1.0, 1.0)
            outdata[:] = mixed
            
        except Exception as e:
            logging.error(f"Audio callback error: {e}")
            outdata.fill(0)

    def note_on(self, note, velocity):
        """Start playing a note"""
        try:
            if (note, velocity, 1) in gv.samples:
                gv.samples[note, velocity, 1][0].play(note, velocity)
        except Exception as e:
            logging.error(f"Note on error: {e}")

    def note_off(self, note):
        """Stop playing a note"""
        for sound in gv.playingsounds[:]:
            if sound.note == note:
                sound.fadeout = True

    def cleanup(self):
        """Clean up audio resources"""
        if self.stream:
            self.stream.stop()
            self.stream.close()
