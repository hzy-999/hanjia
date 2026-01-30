# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

mijiaAPI is a Python library for controlling Xiaomi Mijia (Mi Home) smart devices. It provides both a Python API and a CLI tool for device control, scene management, and statistics retrieval.

## Common Commands

### Installation (Development)
```bash
pip install -e .                    # Editable install
uv sync                             # If using uv
```

### Running the CLI
```bash
mijiaAPI --help                     # Show help
mijiaAPI -l                         # List all devices
mijiaAPI --list_homes               # List homes
mijiaAPI get --dev_name "灯" --prop_name "brightness"
mijiaAPI set --dev_name "灯" --prop_name "on" --value True
```

### Linting
```bash
ruff check .                        # Run linter
ruff format .                       # Format code
```

### Testing
```bash
pytest tests/                       # Run all tests
pytest tests/integration/           # Run integration tests only
```

## Architecture

### Core Library (`mijiaAPI/`)
- **`apis.py`** - HTTP request handling to Mijia cloud API, authentication, and raw API methods
- **`devices.py`** - Two main classes:
  - `mijiaAPI`: Low-level API using raw siid/piid (Service ID/Property ID)
  - `mijiaDevice`: High-level OOP wrapper that abstracts siid/piid details, allows attribute-style access (e.g., `device.brightness = 60`)
- **`errors.py`** - Custom exceptions: `LoginError`, `DeviceNotFoundError`, `DeviceGetError`, `DeviceSetError`, `DeviceActionError`, `APIError`
- **`__main__.py`** - CLI implementation (`cli` function)

### Key Patterns
- **Authentication**: QR code login, credentials saved to `~/.config/mijia-api/auth.json` by default
- **Device specs**: Fetched from `home.miot-spec.com` via `get_device_info(model)`
- **Batch operations**: `get_devices_prop` and `set_devices_prop` accept lists for bulk operations
- **Property access**: Properties with `-` in names use `_` in Python (e.g., `color-temperature` → `color_temperature`)

### Additional Components
- **`decrypt/`** - Tools for decrypting API traffic
- **`demos/`** - Example scripts
- **`tools/`** - Diagnostic utilities (`diagnose.py`, `inspect_model.py`)
- **`ui/desktop/`** - AquaGuard desktop application (PyQt-based)
- **`ui/firmware/`** - ESP32/ESP8266 Arduino firmware for custom hardware

## Code Style
- Line length: 100 characters
- Formatter: ruff with double quotes, space indentation
- Import sorting: 2 blank lines after imports (isort via ruff)
