# Maintenance log

## 2.0 architecture reset

- Replaced the Click-only interface with a Textual TUI plus Typer administration CLI.
- Replaced the custom scheduler with official `py-fsrs`.
- Replaced mutable JSON storage with per-device append-only events and a rebuildable local SQLite projection.
- Delegated multi-device transport to external folder synchronization tools.
- Moved credentials to the device keyring with an environment-only fallback.
- Started a new data format; legacy JSON migration is intentionally unsupported.

See the Git history for pre-2.0 maintenance notes.

## 2.0 distribution and settings

- Added a versioned `leetcode-fsrs-bin` AUR channel alongside `leetcode-fsrs-git`.
- Added an Application Launcher Desktop Entry to both Arch packages.
- Made common Study Preferences and Device Settings editable from separate TUI sections.
- Added stale-form conflict detection and replicated preference validation.
- Completed the TUI's Chinese and English fixed interface text.
