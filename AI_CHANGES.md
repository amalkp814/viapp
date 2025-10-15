# AI Changes Log

This file records changes made by the AI assistant (code edits, behavior changes, and configuration updates).

Each entry includes date, files modified, and a short description of the change.

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
