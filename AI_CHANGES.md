# AI Changes Log

This file records changes made by the AI assistant (code edits, behavior changes, and configuration updates).

Each entry includes date, files modified, and a short description of the change.

---

2025-10-31 — AI edits

- **Project Refactor**: Simplified the application to its core "voice keyboard" functionality.
- **Removed Features**: Deleted batch processing (`src/batch_thread.py`) and related UI elements (`src/ui/main_window.py`, `src/main.py`).
- **Dependencies**: Cleaned up dependencies in `new_requirement.txt` (removed `soundfile`).
- **Documentation**: Rewrote `README.md` and `CHANGELOG.md` to align with the new, focused scope of the project.
- **Bug Fixes**:
    - Downgraded `onnxruntime` to `1.17.0` to fix a DLL loading issue on Windows.
    - Implemented a configuration migration in `src/utils.py` to automatically update VAD settings for existing users.

---

2025-10-15 — AI edits

- Modified `src/result_thread.py`: improved noise detection (normalized RMS), added per-frame energy fallback, added `max_recording_duration_ms` enforcement and `vad_aggressiveness` config support.

- Modified `src/key_listener.py`: added future annotations import and typing imports to avoid runtime annotation evaluation issues.

- Modified `src/input_simulation.py`: added best-effort Windows foreground helper.

- Modified `src/main.py`: defensive attribute initialization and defensive cleanup logic; wired start/stop recording signals.

- Updated `README.md` to list new config options.

- Created `AI_CHANGES.md` (this file).

---

(End of log)
