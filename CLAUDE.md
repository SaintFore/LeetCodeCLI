# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LeetCode FSRS CLI is a Python CLI application that implements a spaced repetition system (FSRS v4 algorithm) for LeetCode problem practice. The project is structured as a modular Python package with a clean separation of concerns.

**当前状态**: 项目已完成并成功发布到AUR和GitHub

## Architecture

### Core Components
- **CLI Interface** (`leetcode_fsrs_cli/cli.py`): Click-based command-line interface
- **FSRS Algorithm** (`leetcode_fsrs_cli/fsrs.py`): FSRS v4 spaced repetition implementation
- **Question Management** (`leetcode_fsrs_cli/leetcode.py`): Question data models and operations
- **Review Scheduling** (`leetcode_fsrs_cli/scheduler.py`): Review prioritization and session management
- **Data Storage** (`leetcode_fsrs_cli/storage.py`): JSON-based persistence using XDG standard directories
- **Authentication** (`leetcode_fsrs_cli/auth.py`): Cookie-based authentication management
- **API Client** (`leetcode_fsrs_cli/leetcode_api.py`): LeetCode GraphQL API client
- **Synchronization** (`leetcode_fsrs_cli/sync.py`): Data synchronization logic

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
leetcode-fsrs init
leetcode-fsrs auth login  # New
leetcode-fsrs sync        # New
leetcode-fsrs practice
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
- Commands: `init`, `practice`, `stats`, `list`, `search`, `schedule`, `add`
- Uses Click framework for command-line interface

### FSRS Algorithm Parameters
- Memory retention target: 90%
- Difficulty range: 1-10
- Rating system: 1-5 (forgetting to perfect recall)
- Maximum interval: 36500 days

### Data Storage
- Location: `~/.config/leetcode-fsrs-cli/`
- Files: `questions.json`, `reviews.json`, `config.json`
- Default sample data included in package

### Configuration
User configurable options in `config.json`:
- `daily_review_limit`: Maximum reviews per day
- `auto_update_due`: Auto-update due reviews
- `show_progress_bar`: Display progress indicators
- `language`: Interface language preference

## Dependencies

### Core Python Dependencies
- click: CLI framework (实际使用)
- requests: HTTP requests (预留，用于未来API集成)

### 依赖优化状态
- ✅ **已清理**: pandas, numpy, rich, tabulate (这些依赖在代码中未实际使用)
- ✅ **精简后**: 从6个依赖减少到2个必需依赖
- ✅ **二进制版本**: 提供零依赖的 `leetcode-fsrs-cli-bin` 包

### System Requirements
- Python 3.8+
- Standard Linux tools for AUR packaging

## Project Structure

```
leetcode-fsrs-cli/
├── leetcode_fsrs_cli/          # Main Python package
│   ├── cli.py                  # CLI interface (入口点)
│   ├── fsrs.py                 # FSRS algorithm
│   ├── leetcode.py             # Question management
│   ├── scheduler.py            # Review scheduling
│   ├── storage.py              # Data persistence
│   └── data/                   # Default configuration data
│       ├── config.json
│       └── questions.json
├── setup.py                    # Package configuration
├── PKGBUILD                    # Arch Linux package script
├── .SRCINFO                    # AUR metadata
├── requirements.txt            # Python dependencies
└── Documentation files
```

## Maintenance Notes

- **Version Updates**: Update both `setup.py` and `PKGBUILD` when changing versions
- **AUR Releases**: Use `makepkg --printsrcinfo > .SRCINFO` to update package metadata
- **Data Migration**: Backward compatibility for JSON data files is important
- **Testing**: Manual testing of all CLI commands required before releases

## Integration Points

- **LeetCode API**: Ready for future integration via `requests` module
- **Storage Backends**: Modular design allows for different persistence layers
- **Algorithm Extensions**: FSRS implementation can be customized or replaced

## Common Development Tasks

1. **Adding New Commands**: Extend `cli.py` with new Click commands
2. **Algorithm Modifications**: Update `fsrs.py` for FSRS parameter changes
3. **Data Model Changes**: Modify `Question` dataclass in `leetcode.py`
4. **Storage Enhancements**: Extend `StorageManager` in `storage.py`

## Release Process

1. Update version in `setup.py` and `PKGBUILD`
2. Build and test package: `makepkg -si`
3. Update `.SRCINFO`: `makepkg --printsrcinfo > .SRCINFO`
4. Commit changes and create release tag
5. Push to AUR repository: `git push aur main`

## 重要提醒

- **AUR双版本**:
  - 源码版: `leetcode-fsrs-cli` (精简依赖)
  - 二进制版: `leetcode-fsrs-cli-bin` (零依赖)
- GitHub仓库: https://github.com/SaintFore/LeetCodeCLI
- 详细维护记录见: `MAINTENANCE_LOG.md`
- AI维护指南见: `AI_MAINTENANCE_GUIDE.md`

## 双版本策略

### 源码版 (`leetcode-fsrs-cli`)
- **依赖**: `python-click`, `python-requests`
- **特点**: 轻量，适合开发者
- **安装**: `paru -S leetcode-fsrs-cli`

### 二进制版 (`leetcode-fsrs-cli-bin`)
- **依赖**: 无 (完全独立)
- **特点**: 零依赖，适合普通用户
- **安装**: `paru -S leetcode-fsrs-cli-bin`