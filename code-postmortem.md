# Viapp Code Postmortem

## Project Overview

Viapp is a desktop application that provides voice-to-text functionality using local AI models. It allows users to dictate text into any application using global hotkeys. The application is built using Python and PyQt5 for the GUI, and it leverages the `faster-whisper` library for efficient local transcription.

## Architecture

The project follows a modular architecture, separating concerns into distinct components:

- **Entry Point**: `run.py` launches the application by executing `src/main.py`.
- **GUI & State Management**: `src/main.py` (viappApp class) manages the application lifecycle, system tray icon, and coordinates between different components.
- **Audio Recording**: `src/result_thread.py` handles audio input using `sounddevice` and detects speech using `webrtcvad`.
- **Transcription**: `src/transcription.py` wraps the `faster-whisper` model to transcribe audio chunks.
- **Input Simulation**: `src/input_simulation.py` simulates keyboard input to type the transcribed text into the active window.
- **Global Hotkeys**: `src/key_listener.py` listens for global key combinations to toggle recording.
- **Configuration**: `src/utils.py` (ConfigManager) handles loading and saving user settings.

## Key Components

### 1. Main Application (`src/main.py`)

- **Class**: `viappApp`
- **Responsibilities**:
  - Initializes the PyQt application.
  - Sets up the system tray icon and context menu.
  - Manages the `ResultThread` for recording and transcription.
  - Handles global hotkey events to toggle recording states.
  - Manages the `SettingsWindow` for user configuration.

### 2. Audio Processing (`src/result_thread.py`)

- **Class**: `ResultThread` (inherits from `QThread`)
- **Responsibilities**:
  - Captures audio from the microphone using `sounddevice`.
  - Uses `webrtcvad` to detect voice activity and filter out silence.
  - Buffers audio frames and yields chunks containing speech.
  - Calls the transcription function for each speech chunk.
  - Emits signals (`statusSignal`, `resultSignal`, `partialResultSignal`) to update the UI.

### 3. Transcription (`src/transcription.py`)

- **Functions**: `create_local_model`, `transcribe_local`, `post_process_transcription`
- **Responsibilities**:
  - Initializes the `faster-whisper` model (supports CPU and GPU).
  - Transcribes audio data (numpy arrays).
  - Applies post-processing rules (e.g., removing trailing periods, capitalization).

### 4. Input Simulation (`src/input_simulation.py`)

- **Classes**: `InputSimulator` (Factory), `_PynputSimulator`, `_YdotoolSimulator`
- **Responsibilities**:
  - Simulates keyboard strokes to type the transcribed text.
  - Supports `pynput` for cross-platform compatibility.
  - Supports `ydotool` for Linux (Wayland) support.
  - Handles text replacement rules defined in the configuration.

### 5. Key Listener (`src/key_listener.py`)

- **Class**: `KeyListener`
- **Responsibilities**:
  - Uses `pynput` to listen for global key presses.
  - Detects activation key combinations (e.g., Ctrl+Alt+K).
  - Triggers callbacks for activation and deactivation events.

### 6. Configuration (`src/utils.py`)

- **Class**: `ConfigManager` (Singleton)
- **Responsibilities**:
  - Loads configuration from `config.yaml` and `config_schema.yaml`.
  - Provides methods to get and set configuration values.
  - Handles saving user preferences.

## Data Flow

1. **Activation**: User presses the hotkey. `KeyListener` triggers `viappApp.on_activation`.
2. **Recording**: `viappApp` starts `ResultThread`. `ResultThread` captures audio and detects speech.
3. **Transcription**: `ResultThread` sends audio chunks to `transcription.transcribe`. `faster-whisper` processes the audio.
4. **Output**: The transcribed text is returned to `ResultThread`, which emits a signal. `viappApp` receives the signal and uses `InputSimulator` to type the text.

## Dependencies

- **PyQt5**: GUI framework.
- **faster-whisper**: Local speech-to-text model.
- **sounddevice**: Audio recording.
- **webrtcvad**: Voice activity detection.
- **pynput**: Global hotkeys and input simulation.
- **PyYAML**: Configuration file parsing.
- **numpy**: Audio data manipulation.

## Future Improvements

- **Model Management**: Add UI for downloading and managing different Whisper models.
- **Real-time Feedback**: Improve the overlay to show real-time partial results more clearly.
- **Audio Device Selection**: Enhance the settings UI to allow easier selection of input devices.
- **Plugin System**: Allow users to write custom post-processing scripts.
