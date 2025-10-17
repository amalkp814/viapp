# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### AI Assistant Edits (2025-10-15)

- Improved audio recording and VAD handling: normalized RMS energy checks, per-frame energy fallback, and `max_recording_duration_ms` enforcement in `src/result_thread.py`.

- Added safe import-time annotations to `src/key_listener.py` and a Windows foreground helper in `src/input_simulation.py`.

- Defensive app initialization and UI wiring changes in `src/main.py` and `src/ui/main_window.py` (merged status into main window, start button toggles recording).

- Updated `README.md` with new config keys and created `AI_CHANGES.md` to track AI-made edits.

### Project Fork and Renaming

- Forked from WhisperWriter ([savbell/whisper-writer](https://github.com/savbell/whisper-writer)) and renamed to **viapp** ([amalkp814/viapp](https://github.com/amalkp814/viapp)).

- Updated all project references, links, and documentation to reflect the new name and repository.

### Added

- New settings window to configure viapp.

- New main window to either start the keyboard listener or open the settings window.

- New continuous recording mode ([Issue #40](https://github.com/amalkp814/viapp/issues/40)).

- New option to play a sound when transcription finishes ([Issue #40](https://github.com/amalkp814/viapp/issues/40)).

- Beginner-friendly comments added to all major source files and configuration files for easier understanding and onboarding.

- Updated `.gitignore` to include all common virtual environment folders and added comments for beginners.

### Changed

- Migrated status window from using `tkinter` to `PyQt5`.

- Migrated from using JSON to using YAML to store configuration settings.

- Upgraded to latest versions of `openai` and `faster-whisper`, including support for local API ([Issue #32](https://github.com/amalkp814/viapp/issues/32)).

- Improved documentation and code comments throughout the project for clarity.

### Removed

- No longer using `keyboard` package to listen for key presses.

## [1.0.1] - 2024-01-28

### Added

- New message to identify whether Whisper was being called using the API or running locally.

- Additional hold-to-talk ([PR #28](https://github.com/savbell/whisper-writer/pull/28)) and press-to-toggle recording methods ([Issue #21](https://github.com/savbell/whisper-writer/issues/21)).

- New configuration options to:

  - Choose recording method (defaulting to voice activity detection).

  - Choose which sound device and sample rate to use.

  - Hide the status window ([PR #28](https://github.com/savbell/whisper-writer/pull/28)).

### Changed

- Migrated from `whisper` to `faster-whisper` ([Issue #11](https://github.com/savbell/whisper-writer/issues/11)).

- Migrated from `pyautogui` to `pynput` ([PR #10](https://github.com/savbell/whisper-writer/pull/10)).

- Migrated from `webrtcvad` to `webrtcvad-wheels` ([PR #17](https://github.com/savbell/whisper-writer/pull/17)).

- Changed default activation key combo from `ctrl+alt+space` to `ctrl+shift+space`.

- Changed to using a local model rather than the API by default.

- Revamped README.md, including new Roadmap, Contributing, and Credits sections.

### Fixed

- Local model is now only loaded once at start-up, rather than every time the activation key combo was pressed.

- Default configuration now auto-chooses compute type for the local model to avoid warnings.

- Graceful degradation to CPU if CUDA isn't available ([PR #30](https://github.com/savbell/whisper-writer/pull/30)).

- Removed long prefix of spaces in transcription ([PR #19](https://github.com/savbell/whisper-writer/pull/19)).

## [1.0.0] - 2023-05-29

### Added

- Initial release of WhisperWriter.

- Added CHANGELOG.md.

- Added Versioning and Known Issues to README.md.

### Changed

- Updated Whisper Python package; the local model is now compatible with Python 3.11.

[Unreleased]: https://github.com/amalkp814/viapp/compare/v1.0.1...HEAD
[1.0.1]: https://github.com/amalkp814/viapp/releases/tag/v1.0.0...v1.0.1
[1.0.0]: https://github.com/amalkp814/viapp/releases/tag/v1.0.0
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### AI Assistant Edits (2025-10-15)

- Improved audio recording and VAD handling: normalized RMS energy checks, per-frame energy fallback, and `max_recording_duration_ms` enforcement in `src/result_thread.py`.

- Added safe import-time annotations to `src/key_listener.py` and a Windows foreground helper in `src/input_simulation.py`.

- Defensive app initialization and UI wiring changes in `src/main.py` and `src/ui/main_window.py` (merged status into main window, start button toggles recording).

- Updated `README.md` with new config keys and created `AI_CHANGES.md` to track AI-made edits.

### Project Fork and Renaming

- Forked from WhisperWriter ([savbell/whisper-writer](https://github.com/savbell/whisper-writer)) and renamed to **viapp** ([amalkp814/viapp](https://github.com/amalkp814/viapp)).

- Updated all project references, links, and documentation to reflect the new name and repository.

### Added

- New settings window to configure viapp.

- New main window to either start the keyboard listener or open the settings window.

- New continuous recording mode ([Issue #40](https://github.com/amalkp814/viapp/issues/40)).

- New option to play a sound when transcription finishes ([Issue #40](https://github.com/amalkp814/viapp/issues/40)).

- Beginner-friendly comments added to all major source files and configuration files for easier understanding and onboarding.

- Updated `.gitignore` to include all common virtual environment folders and added comments for beginners.

### Changed

- Migrated status window from using `tkinter` to `PyQt5`.

- Migrated from using JSON to using YAML to store configuration settings.

- Upgraded to latest versions of `openai` and `faster-whisper`, including support for local API ([Issue #32](https://github.com/amalkp814/viapp/issues/32)).

- Improved documentation and code comments throughout the project for clarity.

### Removed

- No longer using `keyboard` package to listen for key presses.

## [1.0.1] - 2024-01-28

### Added

- New message to identify whether Whisper was being called using the API or running locally.

- Additional hold-to-talk ([PR #28](https://github.com/savbell/whisper-writer/pull/28)) and press-to-toggle recording methods ([Issue #21](https://github.com/savbell/whisper-writer/issues/21)).

- New configuration options to:

  - Choose recording method (defaulting to voice activity detection).

  - Choose which sound device and sample rate to use.

  - Hide the status window ([PR #28](https://github.com/savbell/whisper-writer/pull/28)).

### Changed

- Migrated from `whisper` to `faster-whisper` ([Issue #11](https://github.com/savbell/whisper-writer/issues/11)).

- Migrated from `pyautogui` to `pynput` ([PR #10](https://github.com/savbell/whisper-writer/pull/10)).

- Migrated from `webrtcvad` to `webrtcvad-wheels` ([PR #17](https://github.com/savbell/whisper-writer/pull/17)).

- Changed default activation key combo from `ctrl+alt+space` to `ctrl+shift+space`.

- Changed to using a local model rather than the API by default.

- Revamped README.md, including new Roadmap, Contributing, and Credits sections.

### Fixed

- Local model is now only loaded once at start-up, rather than every time the activation key combo was pressed.

- Default configuration now auto-chooses compute type for the local model to avoid warnings.

- Graceful degradation to CPU if CUDA isn't available ([PR #30](https://github.com/savbell/whisper-writer/pull/30)).

- Removed long prefix of spaces in transcription ([PR #19](https://github.com/savbell/whisper-writer/pull/19)).

## [1.0.0] - 2023-05-29

### Added

- Initial release of WhisperWriter.

- Added CHANGELOG.md.

- Added Versioning and Known Issues to README.md.

### Changed

- Updated Whisper Python package; the local model is now compatible with Python 3.11.

[Unreleased]: https://github.com/amalkp814/viapp/compare/v1.0.1...HEAD
[1.0.1]: https://github.com/amalkp814/viapp/releases/tag/v1.0.0...v1.0.1
[1.0.0]: https://github.com/amalkp814/viapp/releases/tag/v1.0.0
# =============================
# Changelog (with comments)
# =============================
# This file lists all notable changes to the project.
# Beginners: Each version section shows what was added, changed, fixed, or removed.
# Follow the format at https://keepachangelog.com/en/1.0.0/
#
# To add a new entry, copy the format and add your changes under the correct version.

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### AI Assistant Edits (2025-10-15)

- Improved audio recording and VAD handling: normalized RMS energy checks, per-frame energy fallback, and `max_recording_duration_ms` enforcement in `src/result_thread.py`.

- Added safe import-time annotations to `src/key_listener.py` and a Windows foreground helper in `src/input_simulation.py`.

- Defensive app initialization and UI wiring changes in `src/main.py` and `src/ui/main_window.py` (merged status into main window, start button toggles recording).

- Updated `README.md` with new config keys and created `AI_CHANGES.md` to track AI-made edits.

### Project Fork and Renaming
- Forked from WhisperWriter ([savbell/whisper-writer](https://github.com/savbell/whisper-writer)) and renamed to **viapp** ([amalkp814/viapp](https://github.com/amalkp814/viapp)).
- Updated all project references, links, and documentation to reflect the new name and repository.

### Added
- New settings window to configure viapp.
- New main window to either start the keyboard listener or open the settings window.
- New continuous recording mode ([Issue #40](https://github.com/amalkp814/viapp/issues/40)).
- New option to play a sound when transcription finishes ([Issue #40](https://github.com/amalkp814/viapp/issues/40)).
- Beginner-friendly comments added to all major source files and configuration files for easier understanding and onboarding.
- Updated `.gitignore` to include all common virtual environment folders and added comments for beginners.

### Changed
- Migrated status window from using `tkinter` to `PyQt5`.
- Migrated from using JSON to using YAML to store configuration settings.
- Upgraded to latest versions of `openai` and `faster-whisper`, including support for local API ([Issue #32](https://github.com/amalkp814/viapp/issues/32)).
- Improved documentation and code comments throughout the project for clarity.

### Removed
- No longer using `keyboard` package to listen for key presses.

## [1.0.1] - 2024-01-28
### Added
- New message to identify whether Whisper was being called using the API or running locally.
- Additional hold-to-talk ([PR #28](https://github.com/savbell/whisper-writer/pull/28)) and press-to-toggle recording methods ([Issue #21](https://github.com/savbell/whisper-writer/issues/21)).
- New configuration options to:
  - Choose recording method (defaulting to voice activity detection).
## [Unreleased]

### AI Assistant Edits (2025-10-15)

- Improved audio recording and VAD handling: normalized RMS energy checks, per-frame energy fallback, and `max_recording_duration_ms` enforcement in `src/result_thread.py`.

- Added safe import-time annotations to `src/key_listener.py` and a Windows foreground helper in `src/input_simulation.py`.

- Defensive app initialization and UI wiring changes in `src/main.py` and `src/ui/main_window.py` (merged status into main window, start button toggles recording).

- Updated `README.md` with new config keys and created `AI_CHANGES.md` to track AI-made edits.

### Project Fork and Renaming

- Forked from WhisperWriter ([savbell/whisper-writer](https://github.com/savbell/whisper-writer)) and renamed to **viapp** ([amalkp814/viapp](https://github.com/amalkp814/viapp)).

- Updated all project references, links, and documentation to reflect the new name and repository.

### Added

- New settings window to configure viapp.

- New main window to either start the keyboard listener or open the settings window.

- New continuous recording mode ([Issue #40](https://github.com/amalkp814/viapp/issues/40)).

- New option to play a sound when transcription finishes ([Issue #40](https://github.com/amalkp814/viapp/issues/40)).

- Beginner-friendly comments added to all major source files and configuration files for easier understanding and onboarding.

- Updated `.gitignore` to include all common virtual environment folders and added comments for beginners.

### Changed

- Migrated status window from using `tkinter` to `PyQt5`.

- Migrated from using JSON to using YAML to store configuration settings.

- Upgraded to latest versions of `openai` and `faster-whisper`, including support for local API ([Issue #32](https://github.com/amalkp814/viapp/issues/32)).

- Improved documentation and code comments throughout the project for clarity.

### Removed

- No longer using `keyboard` package to listen for key presses.
  - Choose which sound device and sample rate to use.
  - Hide the status window ([PR #28](https://github.com/savbell/whisper-writer/pull/28)).

### Changed
- Migrated from `whisper` to `faster-whisper` ([Issue #11](https://github.com/savbell/whisper-writer/issues/11)).
- Migrated from `pyautogui` to `pynput` ([PR #10](https://github.com/savbell/whisper-writer/pull/10)).
- Migrated from `webrtcvad` to `webrtcvad-wheels` ([PR #17](https://github.com/savbell/whisper-writer/pull/17)).
- Changed default activation key combo from `ctrl+alt+space` to `ctrl+shift+space`.
- Changed to using a local model rather than the API by default.
- Revamped README.md, including new Roadmap, Contributing, and Credits sections.

### Fixed
- Local model is now only loaded once at start-up, rather than every time the activation key combo was pressed.
- Default configuration now auto-chooses compute type for the local model to avoid warnings.
- Graceful degradation to CPU if CUDA isn't available ([PR #30](https://github.com/savbell/whisper-writer/pull/30)).
- Removed long prefix of spaces in transcription ([PR #19](https://github.com/savbell/whisper-writer/pull/19)).

## [1.0.0] - 2023-05-29
### Added
- Initial release of WhisperWriter.
- Added CHANGELOG.md.
- Added Versioning and Known Issues to README.md.

### Changed
- Updated Whisper Python package; the local model is now compatible with Python 3.11.

[Unreleased]: https://github.com/amalkp814/viapp/compare/v1.0.1...HEAD
[1.0.1]: https://github.com/amalkp814/viapp/releases/tag/v1.0.0...v1.0.1
[1.0.0]: https://github.com/amalkp814/viapp/releases/tag/v1.0.0
