# BearSamplr

A modern Raspberry Pi sampler using Pirate Audio Line Out.

## Hardware Requirements

- Raspberry Pi 3B+
- Pirate Audio Line Out HAT
- MIDI Controller (optional)

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

## Dependencies

- Python 3.11.2
- Debian GNU/Linux 12 (bookworm)
- See requirements.txt for Python package dependencies

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

