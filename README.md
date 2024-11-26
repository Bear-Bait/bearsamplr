# BearSamplr

A modern Raspberry Pi sampler using Pirate Audio Line Out.

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

## Features

- High-quality audio via PCM5102A DAC
- 240x240 ST7789 display interface
- Real-time sample playback
- MIDI input support
- Customizable sample management
- Button control interface

## Dependencies

- Python 3.11.2
- Debian GNU/Linux 12 (bookworm)
- See requirements.txt for Python package dependencies:
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

## License

[MIT License](LICENSE)

## Development Status

Active development - Building core functionality for audio processing and display interface.
