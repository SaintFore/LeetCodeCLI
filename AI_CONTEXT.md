# AI_CONTEXT.md

This file provides context and guidance for AI assistants working on this repository.

## Project Overview

**LeetCode FSRS CLI** is a Python CLI application that implements a spaced repetition system (FSRS v4 algorithm) for LeetCode problem practice. The project is structured as a modular Python package with a clean separation of concerns.

**Current Status**: Project is complete and published to AUR and GitHub.

## Architecture

### Core Components
- **CLI Interface** (`leetcode_fsrs_cli/cli.py`): Click-based command-line interface.
- **FSRS Algorithm** (`leetcode_fsrs_cli/fsrs.py`): FSRS v4 spaced repetition implementation.
- **Question Management** (`leetcode_fsrs_cli/leetcode.py`): Question data models and operations.
- **Review Scheduling** (`leetcode_fsrs_cli/scheduler.py`): Review prioritization and session management.
- **Data Storage** (`leetcode_fsrs_cli/storage.py`): JSON-based persistence using XDG standard directories.
- **Authentication** (`leetcode_fsrs_cli/auth.py`): Cookie-based authentication management.
- **API Client** (`leetcode_fsrs_cli/leetcode_api.py`): LeetCode GraphQL API client.
- **Synchronization** (`leetcode_fsrs_cli/sync.py`): Data synchronization logic.

**Note**: `lcf` is available as a short alias for `leetcode-fsrs`.

### Data Flow
```
User Input → CLI → Auth/Sync/Logic → FSRS Algorithm → Storage
```

## Development Commands

### Installation & Setup
```bash
# Development installation
pip install -e .

# Production installation
pip install .

# AUR package build (Arch Linux)
makepkg -si
```

### Testing & Validation
```bash
# Test CLI commands
leetcode-fsrs --help
leetcode-fsrs auth login
leetcode-fsrs sync
leetcode-fsrs practice --show-content
leetcode-fsrs stats

# Run integration tests
python3 tests/test_real_cookie.py
python3 tests/test_sync_real.py

# Verify data persistence
ls -la ~/.config/leetcode-fsrs-cli/
```

### Package Management
```bash
# Update dependencies
pip install -r requirements.txt

# Build distribution packages
python setup.py sdist bdist_wheel

# AUR package update
makepkg --printsrcinfo > .SRCINFO
```

## Key Implementation Details

### CLI Command Structure
- Main entry point: `leetcode_fsrs_cli/cli:cli`
- Commands: `practice`, `stats`, `list`, `info`, `auth`, `sync`, `config`
- Uses Click framework for command-line interface

### FSRS Algorithm Parameters
- Memory retention target: 90%
- Difficulty range: 1-10
- Rating system: 1-5 (forgetting to perfect recall)
- Maximum interval: 36500 days

### Data Storage
- Location: `~/.config/leetcode-fsrs-cli/`
- Files: `questions.json`, `reviews.json`, `config.json`, `sync_state.json`
- Default sample data included in package

### Configuration
User configurable options in `config.json`:
- `daily_review_limit`: Maximum reviews per day
- `fsrs_params`: Custom FSRS parameters

## Dependencies

### Core Python Dependencies
- click: CLI framework
- requests: HTTP requests

### Dependency Optimization
- Reduced from 6 to 2 essential dependencies.
- Binary version (`leetcode-fsrs-cli-bin`) available with zero dependencies.

## Project Structure

```
leetcode-fsrs-cli/
├── leetcode_fsrs_cli/          # Main Python package
│   ├── cli.py                  # CLI interface (Entry point)
│   ├── fsrs.py                 # FSRS algorithm
│   ├── leetcode.py             # Question management
│   ├── scheduler.py            # Review scheduling
│   ├── storage.py              # Data persistence
│   ├── auth.py                 # Authentication
│   ├── sync.py                 # Synchronization
│   ├── leetcode_api.py         # API Client
│   └── data/                   # Default configuration data
├── setup.py                    # Package configuration
├── aur-assets/                 # AUR package files
│   ├── PKGBUILD                # Arch Linux package script
│   └── .SRCINFO                # AUR metadata
├── requirements.txt            # Python dependencies
└── Documentation files
```

## Maintenance Notes

- **Version Updates**: Update both `setup.py` and `PKGBUILD` when changing versions.
- **AUR Releases**: Use `makepkg --printsrcinfo > .SRCINFO` to update package metadata.
- **Data Migration**: Backward compatibility for JSON data files is important.
- **Testing**: Manual testing of all CLI commands required before releases.
- **ID Migration**: `sync.py` handles migration from internal IDs to frontend IDs.

## Important Links

- **GitHub Repository**: https://github.com/SaintFore/LeetCodeCLI
- **AUR Package (Source)**: https://aur.archlinux.org/packages/leetcode-fsrs-cli
- **AUR Package (Binary)**: https://aur.archlinux.org/packages/leetcode-fsrs-cli-bin
- **Maintenance Log**: `MAINTENANCE_LOG.md`