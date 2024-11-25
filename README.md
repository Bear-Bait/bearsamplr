# BearSampler

A modern sampler/synthesizer application for Raspberry Pi with Pirate Audio HAT.

## Overview

BearSampler is a fork of SamplerBox optimized for the Raspberry Pi 3B+ with Pirate Audio line-out HAT. Key improvements include:

- Modern PyQt/PySide UI with 240x240 display
- Real-time DSP effects (reverb, delay, EQ)
- Improved sample playback engine
- Better memory management
- Hardware-accelerated visualizations

## Planned Improvements

### Display/UI
- Replace text UI with PyQt/PySide interface 
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

### Features
- Sample editing
- MIDI learn functionality
- Preset management
- Extended audio format support
- Memory optimization

## Installation

```bash
# Create virtual environment
python -m venv /opt/bearsampler/venv
source /opt/bearsampler/venv/bin/activate

# Install dependencies
pip install numpy pillow psutil rtmidi2 RPi.GPIO st7789
```

## Requirements

- Raspberry Pi 3B+
- Pirate Audio Line-out HAT
- Arch Linux ARM
- Python 3.9+
- Required packages: numpy, pillow, psutil, rtmidi2, RPi.GPIO, st7789

## License

GNU GPL v3

## Contributing

Pull requests welcome! Please read CONTRIBUTING.md for guidelines.

## Credits

Based on the original [SamplerBox](https://github.com/hansehv/SamplerBox) by Joseph Ernest and Hans Hommersom.
# bearsamplr
