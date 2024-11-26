# BearSamplr

A modern sampler/synthesizer application for Raspberry Pi with Pirate Audio HAT, inspired by SamplerBox.

## Overview

BearSamplr is optimized for the Raspberry Pi 3B+ with Pirate Audio line-out HAT. Key improvements include:
- Modern display interface with 240x240 ST7789
- Real-time DSP effects (planned)
- Improved sample playback engine
- Better memory management
- Hardware-accelerated visualizations

## Hardware Requirements

- Raspberry Pi 3B+
- Pirate Audio Line Out HAT (PCM5102A DAC)
- MIDI Controller (optional)

## System Requirements

- Python 3.11.2
- Debian GNU/Linux 12 (bookworm) aarch64
- Kernel: 6.6.51+rpt-rpi-v8

## Installation

```bash
# Clone the repository
git clone https://github.com/Bear-Bait/bearsamplr.git
cd bearsamplr

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Current Features

- High-quality audio via PCM5102A DAC
- 240x240 ST7789 display interface
- Real-time sample playback
- MIDI input support
- Customizable sample management
- Button control interface

## Planned Improvements

### Display/UI
- Audio waveform visualization
- Real-time EQ display
- Clean hardware button integration

### Audio Engine
- DSP effects pipeline using numpy/scipy
- Interpolated sample playback
- Voice allocation with polyphony limiting
- ADSR envelope implementation
- Multi-threaded audio processing

### Architecture
- MVC pattern implementation
- Async file operations
- Type hints and docstrings
- Unit test coverage
- Python packaging improvements

## Dependencies

- Python 3.11.2
- Debian GNU/Linux 12 (bookworm)
- Core packages:
  - pygame
  - st7789
  - RPi.GPIO
  - Pillow
  - sounddevice
  - numpy
  - python-rtmidi

## Project Structure

```
bearsamplr/
├── src/           # Source code
├── tests/         # Test files
├── docs/          # Documentation
├── config/        # Configuration files
└── requirements.txt  # Project dependencies
```

## Development Status

Active development - Building core functionality for audio processing and display interface.

## License

[MIT License](LICENSE)

## Credits

Based on concepts from the original [SamplerBox](https://github.com/hansehv/SamplerBox) by Joseph Ernest and Hans Hommersom.
