##!/usr/bin/env python3

import os
import math
import random
import pygame
import st7789
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from time import sleep, time
import logging
from datetime import datetime
import sounddevice as sd
import numpy as np
import rtmidi
from pathlib import Path
import subprocess
import multiprocessing

# Set up logging
log_filename = f"bearsampler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Hardware Configuration
HARDWARE_CONFIG = {
    # Display Configuration
    'DISPLAY': {
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

    # Audio Configuration
    'AUDIO': {
        'DEVICE_NAME': 'PirateAudio',
        'SAMPLE_RATE': 44100,
        'CHANNELS': 2,
        'BLOCKSIZE': 1024,
        'FORMAT': 'float32',
        'DAC_SETTINGS': {
            'GPIO_SETTINGS': {
                'BCK': 18,
                'LRCK': 19,
                'DIN': 20,
                'SOFT_MUTE': 25,
            }
        }
    },

    # Button Configuration
    'BUTTONS': {
        'A': 5,    # Previous/Back
        'B': 6,    # Play/Pause/Select
        'X': 16,   # Next/Forward
        'Y': 24    # Menu/Options
    },

    # System Configuration
    'SYSTEM': {
        'MAX_CPU_PERCENT': 85,
        'MAX_POLYPHONY': 64,
        'ENABLE_OVERCLOCKING': False,
        'AUDIO_PRIORITY': -20,
        'USB_MAX_CURRENT': True
    }
}

# Color Theme
COLORS = {
    'background': (40, 0, 0),      # Deep crystal red
    'text': (255, 220, 220),       # Soft crystal white
    'accent': (255, 0, 0),         # Pure red
    'glow': (255, 40, 40),         # Red glow
    'shadow': (20, 0, 0),          # Deep shadow
    'crystal': (255, 180, 180)     # Crystal highlight
}

class SystemSetup:
    @staticmethod
    def setup_audio_config():
        """Configure system audio settings"""
        config_txt = """
        # Audio Configuration
        dtparam=audio=off
        dtoverlay=hifiberry-dac
        gpio=25=op,dh

        # Display Configuration
        dtoverlay=spi1-3cs
        gpio=13=op,dh

        # System Configuration
        dtparam=spi=on
        dtparam=i2c=on
        gpu_mem=32
        max_usb_current=1
        """

        alsa_config = """
        pcm.!default {
            type hw
            card sndrpihifiberry
        }

        ctl.!default {
            type hw
            card sndrpihifiberry
        }
        """

        # Create configuration files
        config_updates = {
            '/boot/config.txt': config_txt,
            '/etc/asound.conf': alsa_config
        }

        for filepath, content in config_updates.items():
            if not os.path.exists(filepath):
                try:
                    with open(filepath, 'w') as f:
                        f.write(content)
                    logging.info(f"Created {filepath}")
                except Exception as e:
                    logging.error(f"Error creating {filepath}: {e}")

    @staticmethod
    def setup_hardware():
        """Configure hardware components"""
        try:
            # Configure GPIO for DAC
            subprocess.run(['gpio', '-g', 'mode', '25', 'out'])
            subprocess.run(['gpio', '-g', 'write', '25', '1'])

            # Set initial audio levels
            subprocess.run(['amixer', 'sset', 'Digital', '100%'])

            # Configure SPI for display
            subprocess.run(['modprobe', 'spi_bcm2835'])

            logging.info("Hardware configuration completed successfully")
            return True

        except Exception as e:
            logging.error(f"Hardware setup error: {e}")
            return False

    @staticmethod
    def get_optimal_settings():
        """Calculate optimal system settings based on hardware"""
        cpu_count = multiprocessing.cpu_count()

        return {
            'BUFFER_SIZE': 1024,
            'PERIOD_SIZE': 256,
            'MAX_POLYPHONY': min(64, cpu_count * 16),
            'SAMPLE_RATE': 44100,
            'PRELOAD_SAMPLES': True,
            'USE_THREADING': True,
            'PRIORITY': -20,
            'AUDIO_CHUNK_SIZE': 256
        }

    @staticmethod
    def test_audio():
        """Test audio output with a simple sine wave"""
        try:
            sample_rate = 44100
            duration = 1
            frequency = 440
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            test_tone = np.sin(2 * np.pi * frequency * t)

            sd.play(test_tone, sample_rate)
            sd.wait()

            logging.info("Audio test completed successfully")
            return True

        except Exception as e:
            logging.error(f"Audio test failed: {e}")
            return False

class DisplayManager:
    def __init__(self):
        self.width = HARDWARE_CONFIG['DISPLAY']['WIDTH']
        self.height = HARDWARE_CONFIG['DISPLAY']['HEIGHT']
        self.disp = st7789.ST7789(
            height=self.height,
            width=self.width,
            rotation=HARDWARE_CONFIG['DISPLAY']['ROTATION'],
            port=0,
            cs=HARDWARE_CONFIG['DISPLAY']['GPIO']['CS'],
            dc=HARDWARE_CONFIG['DISPLAY']['GPIO']['DC'],
            backlight=HARDWARE_CONFIG['DISPLAY']['GPIO']['BACKLIGHT'],
            spi_speed_hz=HARDWARE_CONFIG['DISPLAY']['SPI_SPEED_HZ']
        )

        self.initialize()

    def initialize(self):
        """Initialize display"""
        try:
            self.disp.begin()
            self.load_fonts()
            logging.info("Display initialized successfully")
        except Exception as e:
            logging.error(f"Display initialization error: {e}")
            raise

    def load_fonts(self):
        """Load system fonts or fall back to default"""
        try:
            self.font_large = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
            self.font_medium = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
            self.font_small = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        except Exception as e:
            logging.warning(f"Could not load system fonts: {e}")
            self.font_large = ImageFont.load_default()
            self.font_medium = ImageFont.load_default()
            self.font_small = ImageFont.load_default()

class AudioEngine:
    def __init__(self, config):
        self.sample_rate = config['AUDIO']['SAMPLE_RATE']
        self.channels = config['AUDIO']['CHANNELS']
        self.blocksize = config['AUDIO']['BLOCKSIZE']
        self.format = config['AUDIO']['FORMAT']
        self.stream = None
        self.playing_notes = {}
        self.volume = 0.8
        self.samples = {}

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

            # Mix all active notes
            for note_id, note_data in list(self.playing_notes.items()):
                pos = note_data['position']
                sample = note_data['sample']
                velocity = note_data['velocity']
                release = note_data.get('release', False)

                if pos >= len(sample):
                    del self.playing_notes[note_id]
                    continue

                # Calculate number of samples to mix
                available = len(sample) - pos
                n_samples = min(frames, available)

                # Apply volume and velocity scaling
                gain = (velocity / 127.0) * self.volume
                if release:
                    # Apply release envelope
                    release_samples = note_data['release_samples']
                    release_pos = note_data['release_pos']
                    env = np.linspace(1.0, 0.0, release_samples)[release_pos:release_pos+n_samples]
                    gain *= env[:n_samples]
                    note_data['release_pos'] += n_samples

                # Mix into output buffer
                mixed[:n_samples] += sample[pos:pos+n_samples] * gain

                # Update position
                note_data['position'] += n_samples

            # Prevent clipping
            mixed = np.clip(mixed, -1.0, 1.0)
            outdata[:] = mixed

        except Exception as e:
            logging.error(f"Audio callback error: {e}")
            outdata.fill(0)

    def note_on(self, note, velocity):
        """Start playing a note"""
        if note in self.samples:
            note_id = f"{note}_{time()}"
            self.playing_notes[note_id] = {
                'sample': self.samples[note],
                'position': 0,
                'velocity': velocity,
                'release': False
            }

    def note_off(self, note):
        """Stop playing a note with release"""
        release_time = 0.1  # seconds
        release_samples = int(release_time * self.sample_rate)

        for note_id in list(self.playing_notes.keys()):
            if note_id.startswith(f"{note}_"):
                self.playing_notes[note_id]['release'] = True
                self.playing_notes[note_id]['release_samples'] = release_samples
                self.playing_notes[note_id]['release_pos'] = 0

    def set_volume(self, volume):
        """Set master volume"""
        self.volume = max(0.0, min(1.0, volume))

    def cleanup(self):
        """Clean up audio resources"""
        if self.stream:
            self.stream.stop()
            self.stream.close()


class MIDIHandler:
    def __init__(self, audio_engine):
        self.audio_engine = audio_engine
        self.midi_in = None
        self.active_notes = set()
        self.channel = 0  # MIDI channel 1

    def initialize(self):
        """Initialize MIDI input"""
        try:
            self.midi_in = rtmidi.MidiIn()
            ports = self.midi_in.get_ports()

            if ports:
                self.midi_in.open_port(0)
                self.midi_in.set_callback(self.midi_callback)
                logging.info(f"MIDI initialized: {ports[0]}")
                return True
            else:
                logging.warning("No MIDI ports available")
                return False

        except Exception as e:
            logging.error(f"MIDI initialization error: {e}")
            return False

    def midi_callback(self, message, timestamp):
        """Handle incoming MIDI messages"""
        try:
            msg_type = message[0][0] & 0xF0
            msg_channel = message[0][0] & 0x0F

            if msg_channel == self.channel:
                if msg_type == 0x90:  # Note On
                    note = message[0][1]
                    velocity = message[0][2]
                    if velocity > 0:
                        self.audio_engine.note_on(note, velocity)
                        self.active_notes.add(note)
                    else:
                        self.audio_engine.note_off(note)
                        self.active_notes.discard(note)

                elif msg_type == 0x80:  # Note Off
                    note = message[0][1]
                    self.audio_engine.note_off(note)
                    self.active_notes.discard(note)

                elif msg_type == 0xB0:  # Control Change
                    control = message[0][1]
                    value = message[0][2]
                    self.handle_control_change(control, value)

        except Exception as e:
            logging.error(f"MIDI callback error: {e}")

    def handle_control_change(self, control, value):
        """Process MIDI control change messages"""
        if control == 7:  # Volume
            self.audio_engine.set_volume(value / 127.0)
        # Add more control handlers as needed

    def cleanup(self):
        """Clean up MIDI resources"""
        if self.midi_in:
            self.midi_in.close_port()
            self.midi_in = None


class SampleManager:
    def __init__(self, audio_engine):
        self.audio_engine = audio_engine
        self.sample_path = Path("/media/usb/BearSampler")
        self.current_preset = 0

    def load_preset(self, preset_number):
        """Load samples for the specified preset"""
        try:
            preset_dir = self.sample_path / str(preset_number)
            if not preset_dir.exists():
                logging.warning(f"Preset directory not found: {preset_dir}")
                return False

            # Clear existing samples
            self.audio_engine.samples.clear()

            # Load new samples
            for sample_file in preset_dir.glob("*.wav"):
                try:
                    note = self.get_note_from_filename(sample_file.name)
                    if note is not None:
                        audio_data, _ = sd.read(str(sample_file))
                        if len(audio_data.shape) == 1:
                            # Convert mono to stereo
                            audio_data = np.column_stack((audio_data, audio_data))
                        self.audio_engine.samples[note] = audio_data
                except Exception as e:
                    logging.error(f"Error loading sample {sample_file}: {e}")

            self.current_preset = preset_number
            logging.info(f"Loaded preset {preset_number} with {len(self.audio_engine.samples)} samples")
            return True

        except Exception as e:
            logging.error(f"Error loading preset {preset_number}: {e}")
            return False

    @staticmethod
    def get_note_from_filename(filename):
        """Extract MIDI note number from filename"""
        # Implement note number extraction based on your naming convention
        # Example: "piano_c4.wav" -> 60 (middle C)
        # This is a placeholder - implement your own logic
        try:
            note = int(filename.split('_')[1].split('.')[0])
            return note
        except:
            return None

class Visualizer:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.viz_bars = 12
        self.viz_heights = [0] * self.viz_bars
        self.viz_targets = [0] * self.viz_bars
        self.viz_speed = 0.3

    def update(self, audio_engine):
        """Update visualization based on currently playing notes"""
        if audio_engine.playing_notes:
            for i in range(self.viz_bars):
                if random.random() < 0.3:
                    self.viz_targets[i] = random.uniform(0.3, 1.0)
                diff = self.viz_targets[i] - self.viz_heights[i]
                self.viz_heights[i] += diff * self.viz_speed
        else:
            for i in range(self.viz_bars):
                self.viz_heights[i] = max(0, self.viz_heights[i] - 0.05)
                self.viz_targets[i] = 0

    def draw(self, draw, base_y):
        """Draw visualization bars with fire effect"""
        bar_width = (self.width - 40) // self.viz_bars
        bar_spacing = 4
        max_bar_height = 60

        for i in range(self.viz_bars):
            bar_height = int(self.viz_heights[i] * max_bar_height)
            if bar_height > 0:
                x = 20 + i * (bar_width + bar_spacing)
                for h in range(bar_height):
                    height_percent = h / max_bar_height
                    color = self.get_fire_color(height_percent)
                    draw.line(
                        [(x, base_y - h), (x + bar_width - bar_spacing, base_y - h)],
                        fill=color
                    )

                    # Add flicker effect
                    if h == bar_height - 1 and random.random() < 0.3:
                        flicker_height = random.randint(2, 5)
                        for fh in range(flicker_height):
                            flicker_color = self.get_fire_color(min(1.0, height_percent + 0.2))
                            if random.random() < 0.7:
                                draw.line(
                                    [(x, base_y - h - fh),
                                     (x + bar_width - bar_spacing, base_y - h - fh)],
                                    fill=flicker_color
                                )

    @staticmethod
    def get_fire_color(height_percent):
        """Generate a color in the fire spectrum based on height percentage"""
        if height_percent < 0.2:
            return (min(255, int(height_percent * 5 * 255)), 0, 0)
        elif height_percent < 0.4:
            return (255, int((height_percent - 0.2) * 5 * 255), 0)
        elif height_percent < 0.6:
            return (255, 255, int((height_percent - 0.4) * 5 * 255))
        else:
            intensity = int((height_percent - 0.6) * 2.5 * 255)
            return (255, 255, min(255, 128 + intensity))


class UIManager:
    def __init__(self, display_manager, width, height):
        self.display = display_manager
        self.width = width
        self.height = height
        self.visualizer = Visualizer(width, height)
        self.scroll_position = 0
        self.scroll_speed = 2
        self.scroll_pause = 30
        self.scroll_pause_counter = 0
        self.scroll_width = 200

    def create_base_image(self):
        """Create base image with background gradient"""
        image = Image.new('RGB', (self.width, self.height), COLORS['background'])
        draw = ImageDraw.Draw(image)

        # Add crystal gradient overlay
        for y in range(self.height - 100, self.height):
            opacity = int((y - (self.height - 100)) / 100 * 160)
            color = (80, 0, 0)
            draw.line([(0, y), (self.width, y)], fill=color)

        return image, draw

    def draw_scrolling_text(self, draw, text, x, y, font, fill_color, shadow_color):
        """Draw scrolling text with shadow effect"""
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]

        if text_width > self.scroll_width:
            if self.scroll_pause_counter > 0:
                self.scroll_pause_counter -= 1
                effective_pos = 0
            else:
                effective_pos = -self.scroll_position
                self.scroll_position += self.scroll_speed
                if self.scroll_position > text_width + 20:
                    self.scroll_position = 0
                    self.scroll_pause_counter = self.scroll_pause

            # Draw shadow
            draw.text((x + 2 + effective_pos, y + 2), text, font=font, fill=shadow_color)
            # Draw text
            draw.text((x + effective_pos, y), text, font=font, fill=fill_color)
        else:
            x = x + (self.scroll_width - text_width) // 2
            draw.text((x + 2, y + 2), text, font=font, fill=shadow_color)
            draw.text((x, y), text, font=font, fill=fill_color)

    def update_display(self, state):
        """Update display with current state"""
        image, draw = self.create_base_image()

        # Update visualization
        self.visualizer.update(state.audio_engine)
        self.visualizer.draw(draw, self.height - 10)

        # Draw preset information
        preset_text = f"Preset: {state.sample_manager.current_preset}"
        draw.text((20, 20), preset_text, font=self.display.font_medium, fill=COLORS['text'])

        # Draw active notes
        notes_text = f"Active Notes: {len(state.audio_engine.playing_notes)}"
        draw.text((20, 60), notes_text, font=self.display.font_small, fill=COLORS['text'])

        # Draw volume
        vol_text = f"Volume: {int(state.audio_engine.volume * 100)}%"
        draw.text((20, 100), vol_text, font=self.display.font_small, fill=COLORS['crystal'])

        # Draw MIDI status
        midi_text = "MIDI: Connected" if state.midi_handler.midi_in else "MIDI: Not Connected"
        draw.text((20, 140), midi_text, font=self.display.font_small,
                 fill=COLORS['glow'] if state.midi_handler.midi_in else COLORS['accent'])

        # Draw current time
        time_text = datetime.now().strftime("%H:%M:%S")
        draw.text((20, 180), time_text, font=self.display.font_small, fill=COLORS['text'])

        # Update display
        self.display.disp.display(image)


class InputHandler:
    def __init__(self, buttons_config):
        self.buttons = buttons_config
        self.long_press_time = 0.5
        self.button_states = {
            'A': {'pressed': False, 'time': 0},
            'B': {'pressed': False, 'time': 0},
            'X': {'pressed': False, 'time': 0},
            'Y': {'pressed': False, 'time': 0}
        }

    def initialize(self):
        """Initialize GPIO for buttons"""
        try:
            GPIO.setmode(GPIO.BCM)
            for button in self.buttons.values():
                GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            return True
        except Exception as e:
            logging.error(f"Button initialization error: {e}")
            return False

    def check_buttons(self):
        """Check button states and return events"""
        events = []
        current_time = time()

        for name, pin in self.buttons.items():
            button_state = not GPIO.input(pin)
            prev_state = self.button_states[name]

            if button_state and not prev_state['pressed']:
                # Button just pressed
                prev_state['pressed'] = True
                prev_state['time'] = current_time
                events.append((name, 'press'))

            elif button_state and prev_state['pressed']:
                # Check for long press
                if current_time - prev_state['time'] >= self.long_press_time:
                    events.append((name, 'long_press'))
                    prev_state['time'] = current_time

            elif not button_state and prev_state['pressed']:
                # Button released
                prev_state['pressed'] = False
                if current_time - prev_state['time'] < self.long_press_time:
                    events.append((name, 'short_press'))

        return events

    def cleanup(self):
        """Clean up GPIO resources"""
        GPIO.cleanup()

def format_time(seconds):
    """Format time in seconds to MM:SS"""
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"

class BearSamplerState:
    def __init__(self):
        self.is_running = True
        self.is_sleeping = False
        self.last_activity_time = time()
        self.sleep_timeout = 300  # 5 minutes
        self.error_count = 0
        self.current_menu = None


class BearSampler:
    def __init__(self):
        self.state = BearSamplerState()

        # Initialize system
        logging.info("Initializing BearSampler...")
        self.system_setup = SystemSetup()

        # Create core components
        self.display_manager = DisplayManager()
        self.audio_engine = AudioEngine(HARDWARE_CONFIG)
        self.midi_handler = MIDIHandler(self.audio_engine)
        self.sample_manager = SampleManager(self.audio_engine)
        self.ui_manager = UIManager(
            self.display_manager,
            HARDWARE_CONFIG['DISPLAY']['WIDTH'],
            HARDWARE_CONFIG['DISPLAY']['HEIGHT']
        )
        self.input_handler = InputHandler(HARDWARE_CONFIG['BUTTONS'])

    def initialize(self):
        """Initialize all subsystems"""
        try:
            # Configure system
            if not self.system_setup.setup_hardware():
                raise RuntimeError("Hardware setup failed")

            # Initialize display
            self.display_manager.initialize()
            self.show_splash_screen("Initializing...")

            # Initialize audio
            if not self.audio_engine.initialize():
                raise RuntimeError("Audio initialization failed")

            # Initialize MIDI
            self.midi_handler.initialize()  # Don't fail if MIDI isn't available

            # Initialize input
            if not self.input_handler.initialize():
                raise RuntimeError("Input initialization failed")

            # Load initial preset
            if not self.sample_manager.load_preset(0):
                logging.warning("No samples found in initial preset")

            # System test
            if not self.system_setup.test_audio():
                logging.warning("Audio test failed")

            self.show_splash_screen("Ready!")
            sleep(1)

            logging.info("BearSampler initialized successfully")
            return True

        except Exception as e:
            logging.error(f"Initialization error: {e}")
            self.show_error_screen(f"Init Error: {str(e)}")
            return False

    def show_splash_screen(self, message):
        """Display splash screen with message"""
        image = Image.new('RGB', (240, 240), COLORS['background'])
        draw = ImageDraw.Draw(image)

        # Draw logo
        logo_text = "BearSampler"
        draw.text((50, 100), logo_text,
                 font=self.display_manager.font_large,
                 fill=COLORS['crystal'])

        # Draw message
        draw.text((50, 140), message,
                 font=self.display_manager.font_small,
                 fill=COLORS['text'])

        self.display_manager.disp.display(image)

    def show_error_screen(self, error_message):
        """Display error screen"""
        image = Image.new('RGB', (240, 240), COLORS['background'])
        draw = ImageDraw.Draw(image)

        draw.text((20, 100), "Error:",
                 font=self.display_manager.font_large,
                 fill=COLORS['accent'])

        # Word wrap error message
        words = error_message.split()
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            test_line = ' '.join(current_line)
            bbox = draw.textbbox((0, 0), test_line,
                               font=self.display_manager.font_small)
            if bbox[2] - bbox[0] > 200:
                if len(current_line) > 1:
                    lines.append(' '.join(current_line[:-1]))
                    current_line = [word]
                else:
                    lines.append(test_line)
                    current_line = []
        if current_line:
            lines.append(' '.join(current_line))

        y = 140
        for line in lines:
            draw.text((20, y), line,
                     font=self.display_manager.font_small,
                     fill=COLORS['text'])
            y += 20

        self.display_manager.disp.display(image)

    def handle_button_events(self, events):
        """Process button events"""
        for button, event_type in events:
            self.state.last_activity_time = time()

            if self.state.is_sleeping:
                # Wake up from sleep on any button press
                self.state.is_sleeping = False
                continue

            try:
                if event_type == 'short_press':
                    if button == 'A':
                        # Previous preset
                        new_preset = max(0, self.sample_manager.current_preset - 1)
                        self.sample_manager.load_preset(new_preset)

                    elif button == 'B':
                        # Play/Stop test tone
                        self.system_setup.test_audio()

                    elif button == 'X':
                        # Next preset
                        self.sample_manager.load_preset(
                            self.sample_manager.current_preset + 1)

                    elif button == 'Y':
                        # Toggle menu
                        self.state.current_menu = (
                            None if self.state.current_menu else 'main')

                elif event_type == 'long_press':
                    if button == 'Y':
                        # Force sleep mode
                        self.state.is_sleeping = True
                    elif button == 'B':
                        # Restart audio engine
                        self.audio_engine.cleanup()
                        self.audio_engine.initialize()

            except Exception as e:
                logging.error(f"Button handler error: {e}")
                self.show_error_screen(str(e))
                sleep(2)

    def check_sleep_mode(self):
        """Check and update sleep state"""
        if not self.state.is_sleeping:
            if time() - self.state.last_activity_time > self.state.sleep_timeout:
                self.state.is_sleeping = True
                self.show_sleep_screen()

    def show_sleep_screen(self):
        """Display sleep screen"""
        image = Image.new('RGB', (240, 240), (0, 0, 0))
        draw = ImageDraw.Draw(image)

        draw.text((60, 110), "Press any button",
                 font=self.display_manager.font_medium,
                 fill=COLORS['glow'])

        self.display_manager.disp.display(image)

    def run(self):
        """Main program loop"""
        try:
            if not self.initialize():
                return

            logging.info("Starting main loop")
            last_update = time()
            update_interval = 1/30  # 30 FPS

            while self.state.is_running:
                try:
                    # Handle button input
                    events = self.input_handler.check_buttons()
                    if events:
                        self.handle_button_events(events)

                    # Check sleep mode
                    self.check_sleep_mode()

                    # Update display if not sleeping
                    current_time = time()
                    if not self.state.is_sleeping and \
                       current_time - last_update >= update_interval:
                        self.ui_manager.update_display(self)
                        last_update = current_time

                    # Small sleep to prevent CPU overload
                    sleep(0.01)

                except Exception as e:
                    logging.error(f"Loop iteration error: {e}")
                    self.state.error_count += 1
                    if self.state.error_count > 10:
                        raise RuntimeError("Too many errors, shutting down")
                    sleep(1)

        except KeyboardInterrupt:
            logging.info("Received keyboard interrupt")
        except Exception as e:
            logging.error(f"Fatal error: {e}")
            self.show_error_screen(str(e))
            sleep(5)
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up all resources"""
        logging.info("Cleaning up...")
        self.audio_engine.cleanup()
        self.midi_handler.cleanup()
        self.input_handler.cleanup()
        self.show_splash_screen("Shutting down...")
        sleep(1)


if __name__ == "__main__":
    try:
        sampler = BearSampler()
        sampler.run()
    except Exception as e:
        logging.error(f"Main program error: {e}")
        print(f"Fatal error: {e}")
        sys.exit(1)
