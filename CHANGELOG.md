# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [2.0.0] - 2025-10-31

### Changed

- **Major Refactor**: The application has been streamlined to focus exclusively on real-time speech-to-text, functioning as a "voice keyboard."
- **Simplified UI**: The user interface has been simplified, removing all non-essential elements.
- **Removed Features**: Batch processing and other non-core features have been removed to improve focus and performance.
- **Updated Dependencies**: The project's dependencies have been updated and cleaned up.
- **New Documentation**: The `README.md` and `CHANGELOG.md` have been rewritten to reflect the new, simplified nature of the project.

## [1.0.1] - 2024-01-28

### Added

- New message to identify whether Whisper was being called using the API or running locally.
- Additional hold-to-talk and press-to-toggle recording methods.
- New configuration options for recording method, sound device, and sample rate.

### Changed

- Migrated from `whisper` to `faster-whisper`.
- Migrated from `pyautogui` to `pynput`.
- Migrated from `webrtcvad` to `webrtcvad-wheels`.
- Changed default activation key combo from `ctrl+alt+space` to `ctrl+shift+space`.
- Changed to using a local model rather than the API by default.

### Fixed

- Local model is now only loaded once at start-up.
- Default configuration now auto-chooses compute type for the local model.
- Graceful degradation to CPU if CUDA isn't available.
- Removed long prefix of spaces in transcription.

## [1.0.0] - 2023-05-29

### Added

- Initial release of WhisperWriter.
- Added CHANGELOG.md.
- Added Versioning and Known Issues to README.md.

### Changed

- Updated Whisper Python package; the local model is now compatible with Python 3.11.
