# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added

- Redesigned main window with a modern, light theme.
- Implemented live transcription.
- Set F9 as the default global shortcut.
- Added new icons for the application.
- Added `ydotool` as an alternative input simulation method on Linux.
- Added an `auto` input method that uses `ydotool` on Linux if available, otherwise `pynput`.
- Added a `word_replacements` option to the configuration file.
- **Improved VAD**: Implemented silence buffering to preserve natural pauses in speech.
- **Dynamic Threshold**: Added adaptive silence thresholding to better handle different speaking paces.
- **Input Queue**: Implemented a threaded input queue to prevent lost words during rapid dictation.
- **UI Feedback**: Added a "Typing..." state to the main window to indicate background input activity.
- **Reliability**: Added input buffer flushing to ensure all characters are typed immediately.

### Changed

- Renamed the project from "WhisperWriter" to "viapp".
- The application now uses the `small.en` model by default.
- Increased VAD aggressiveness for faster transcriptions.
- The main window now minimizes to the system tray instead of closing.
- The system tray menu is now dynamic, showing "Start/Stop Recording" based on the application's state.

### Fixed

- The application now handles `PortAudioError` gracefully by providing a list of available audio devices and instructions on how to configure them.
- The F9 hotkey and all recording modes now work correctly.

### Removed

- Removed all API-based transcription functionality.
- Removed the old status window.
- Removed the `audioplayer` dependency and related code.
- Removed the `dotenv` dependency and related code.
- Removed the `openai` dependency and related code.

## [1.0.1] - 2024-01-28

### Added

- New message to identify whether Whisper was being called using the API or running locally.
- Additional hold-to-talk ([PR #28](https://github.com/savbell/viapp/pull/28)) and press-to-toggle recording methods ([Issue #21](https://github.com/savbell/viapp/issues/21)).
- New configuration options to:
  - Choose recording method (defaulting to voice activity detection).
  - Choose which sound device and sample rate to use.
  - Hide the status window ([PR #28](https://github.com/savbell/viapp/pull/28)).

### Changed

- Migrated from `whisper` to `faster-whisper` ([Issue #11](https://github.com/savbell/viapp/issues/11)).
- Migrated from `pyautogui` to `pynput` ([PR #10](https://github.com/savbell/viapp/pull/10)).
- Migrated from `webrtcvad` to `webrtcvad-wheels` ([PR #17](https://github.com/savbell/viapp/pull/17)).
- Changed default activation key combo from `ctrl+alt+space` to `ctrl+shift+space`.
- Changed to using a local model rather than the API by default.
- Revamped README.md, including new Roadmap, Contributing, and Credits sections.

### Fixed

- Local model is now only loaded once at start-up, rather than every time the activation key combo was pressed.
- Default configuration now auto-chooses compute type for the local model to avoid warnings.
- Graceful degradation to CPU if CUDA isn't available ([PR #30](https://github.com/savbell/viapp/pull/30)).
- Removed long prefix of spaces in transcription ([PR #19](https://github.com/savbell/viapp/pull/19)).

## [1.0.0] - 2023-05-29

### Added

- Initial release of viapp.
- Added CHANGELOG.md.
- Added Versioning and Known Issues to README.md.

### Changed

- Updated Whisper Python package; the local model is now compatible with Python 3.11.

[Unreleased]: https://github.com/savbell/viapp/compare/v1.0.1...HEAD
[1.0.1]: https://github.com/savbell/viapp/releases/tag/v1.0.0...v1.0.1
[1.0.0]: https://github.com/savbell/viapp/releases/tag/v1.0.0
