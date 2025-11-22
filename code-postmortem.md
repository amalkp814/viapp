# Viapp Code Postmortem: Comprehensive Technical Analysis

## 1. Project Overview

Viapp is a desktop application designed to provide seamless, system-wide voice-to-text functionality. Unlike cloud-based solutions, Viapp runs entirely locally using the `faster-whisper` library, ensuring privacy and low latency. It integrates with the operating system to allow users to dictate text into any active text field (editors, browsers, chat apps) using global hotkeys.

The application is built with **Python 3** and uses **PyQt5** for the Graphical User Interface (GUI). It employs a multi-threaded architecture to ensure the UI remains responsive while handling CPU-intensive audio processing and AI inference tasks.

## 2. System Architecture

The project follows a modular, event-driven architecture. The core logic is separated from the UI, and components communicate primarily through PyQt signals and slots.

### High-Level Modules

1. **Entry Point**: `run.py` / `src/main.py`
2. **GUI Layer**: `src/ui/` (Main Window, Settings, Base Window)
3. **Core Logic**: `src/main.py` (App Controller), `src/key_listener.py` (Global Inputs)
4. **Processing Layer**: `src/result_thread.py` (Audio/VAD), `src/transcription.py` (AI Model)
5. **Output Layer**: `src/input_simulation.py` (Keyboard Emulation)
6. **Infrastructure**: `src/utils.py` (Configuration, Logging)

## 3. Component Deep Dive

### 3.1. Application Controller (`src/main.py`)

The `viappApp` class serves as the central controller.

- **Lifecycle Management**: It initializes the `QApplication`, checks for configuration existence, and decides whether to launch the main UI or the settings window first.
- **Signal Orchestration**: It connects signals from the `MainWindow` (UI events) to the `ResultThread` (logic) and vice-versa.
  - `stateChanged`: A central signal used to propagate state changes (`idle`, `recording`, `transcribing`) to the UI and System Tray.
- **System Tray Integration**: Creates a `QSystemTrayIcon` to allow the app to run in the background. The context menu is dynamically updated based on the app state.
- **Component Initialization**: The `initialize_components` method acts as a dependency injector, spinning up the Input Simulator, Key Listener, and Model only when a valid config exists.

### 3.2. Audio Acquisition & Voice Activity Detection (`src/result_thread.py`)

This is the most complex threading component, handling real-time audio.

- **Audio Input**: Uses `sounddevice` to create an `InputStream`.
  - **Device Fallback**: Implements robust error handling. If the default input device fails, it queries all available devices and attempts to use the first valid input device found.
  - **Callback Mechanism**: Audio is captured in non-blocking callbacks and pushed to a thread-safe `queue.Queue`.
- **Voice Activity Detection (VAD)**: Uses `webrtcvad` to filter silence.
  - **Aggressiveness**: Set to level `3` (most aggressive) to filter out background noise.
  - **Frame Size**: Audio is processed in 30ms chunks (required by WebRTC).
  - **Logic**: It maintains a `speech_detected` flag. It buffers audio frames when speech is detected and yields a complete "sentence" only after a specific duration of silence (`silence_frames`) is observed.
- **Threading**: Inherits from `QThread`. The `run` loop continuously processes the audio queue, ensuring the GUI doesn't freeze during recording or VAD processing.

### 3.3. AI Transcription (`src/transcription.py`)

Wraps the `faster-whisper` library for inference.

- **Model Loading**:
  - **`create_local_model`**: Loads the model based on `config.yaml`. It supports `int8` quantization (forcing CPU) or `float16` (for GPU/CUDA).
  - **Offline Support**: Can load models from a local path if specified, bypassing the Hugging Face download.
- **Preprocessing**:
  - Converts raw `int16` audio data from the microphone into `float32` normalized to the range `[-1, 1]`, which is required by the Whisper model.
- **Inference**:
  - Uses `model.transcribe()` with parameters for language, temperature, and VAD filtering.
- **Post-Processing**:
  - Applies text cleanup rules defined in settings: removing trailing periods, capitalizing/de-capitalizing, and adding trailing spaces.

### 3.4. Input Simulation (`src/input_simulation.py`)

Handles the final output of the text.

- **Factory Pattern**: The `InputSimulator` class acts as a factory, returning either `_PynputSimulator` or `_YdotoolSimulator` based on the OS and configuration.
- **Architecture**:
  - **Threaded Queue**: Implements a producer-consumer pattern using a `queue.Queue` and a background worker thread. This ensures that `typewrite` calls are non-blocking and that multiple transcriptions are typed sequentially without overlapping.
  - **Signals**: Emits `typingStarted` and `typingFinished` signals to keep the UI synchronized with the background typing activity.
- **Strategies**:
  - **`_PynputSimulator`**: Uses `pynput` to simulate key presses. Includes a "force flush" mechanism (simulating a dummy key release) to ensure OS buffers are cleared.
  - **`_YdotoolSimulator`**: Uses `ydotool` (a command-line utility) for Wayland support on Linux.
- **Text Processing**: Before typing, it runs regex-based word replacements (e.g., replacing "comma" with ","), defined in the user config.

### 3.5. Global Key Listener (`src/key_listener.py`)

- **Library**: Uses `pynput.keyboard.Listener`.
- **Logic**: Maintains a `set` of currently pressed keys.
  - **Activation**: Checks if the `pressed_keys` set matches the configured `activation_keys` set.
  - **Debouncing/State**: Triggers `on_activate` only on the rising edge (when the combination is first completed) and `on_deactivate` on the falling edge.

### 3.6. User Interface (`src/ui/`)

- **`BaseWindow`**: A custom `QMainWindow` subclass that implements a frameless, rounded-corner design.
  - **Custom Painting**: Overrides `paintEvent` to draw a rounded rectangle with semi-transparent background using `QPainter`.
  - **Dragging**: Implements custom mouse event handling (`mousePress`, `mouseMove`) to allow dragging the frameless window.
- **`SettingsWindow`**:
  - **Dynamic Generation**: Instead of hardcoding fields, it iterates over the `config_schema.yaml` and `config.yaml` to generate tabs and widgets programmatically. This makes adding new settings trivial (just update the YAML).
  - **Type Mapping**: Maps schema types (`bool`, `str`, `int`) to Qt widgets (`QCheckBox`, `QLineEdit`, etc.).

### 3.7. Configuration Management (`src/utils.py`)

- **Singleton Pattern**: `ConfigManager` ensures only one instance of the config exists.
- **Schema Validation**: Loads a `config_schema.yaml` to define default values and types.
- **Deep Merging**: When loading user config, it performs a deep merge with the defaults, ensuring that missing keys in the user config fall back to safe defaults.

## 4. Data Flow Walkthrough

1. **Initialization**:
    - `viappApp` starts.
    - `ConfigManager` loads defaults + user config.
    - `initialize_components` spins up `KeyListener` and `InputSimulator`.
    - `create_local_model` loads Whisper (heavy operation).

2. **Triggering**:
    - User presses `Ctrl+Alt+K` (default).
    - `KeyListener` detects match -> calls `viappApp.on_activation`.
    - `viappApp` emits `stateChanged("recording")`.
    - `MainWindow` updates icon to red mic.
    - `ResultThread` starts recording.

3. **Recording & VAD**:
    - `ResultThread` reads audio chunks.
    - `webrtcvad` detects speech.
    - Silence counter resets on speech.
    - **Buffering**: Silent frames within active speech are now buffered to preserve natural pauses.
    - When silence > `silence_duration` (dynamic threshold), the chunk is finalized.

4. **Transcription**:
    - `ResultThread` passes the audio chunk to `transcription.transcribe`.
    - `faster-whisper` processes audio -> returns text string.
    - `post_process_transcription` cleans up text.

5. **Output**:
    - `ResultThread` emits `resultSignal(text)`.
    - `viappApp` calls `input_simulator.typewrite(text)`.
    - **Queueing**: Text is added to the input queue (non-blocking).
    - **Typing**: Background worker picks up text, emits `typingStarted` (UI shows "Typing..."), and simulates keystrokes.
    - **Completion**: Worker emits `typingFinished` (UI returns to "Idle").

## 5. Configuration Files

- **`src/config_schema.yaml`**: The source of truth for all available settings and their defaults.
- **`src/config.yaml`**: The user-specific overrides. Generated automatically if missing.

## 6. Error Handling

- **Audio Devices**: If `sounddevice` fails to open the configured device, it iterates through `sd.query_devices()` to find *any* working input device as a fallback.
- **Model Loading**: If GPU loading fails (e.g., missing CUDA), it catches the exception and falls back to CPU (`int8`) automatically.
- **Input Tools**: If `ydotool` is selected but missing, it falls back to `pynput` and logs a warning.

## 7. Dependencies

- **PyQt5**: 5.15.x (GUI)
- **faster-whisper**: 0.10.x (Inference)
- **sounddevice**: 0.4.x (Audio I/O)
- **webrtcvad**: 2.0.x (VAD)
- **pynput**: 1.7.x (IO Hooks)
- **PyYAML**: 6.x (Config)
- **numpy**: 1.x (Data processing)
