
# Voice Keyboard

![version](https://img.shields.io/badge/version-2.0.0-blue)

A simple, real-time speech-to-text application that transcribes your voice into text in any active window, turning your microphone into a voice keyboard.

## How It Works

This application listens for a hotkey (default: `F9`) and, when activated, records your voice, transcribes it using a local Whisper model, and types the text into the currently active application. It's designed to be a simple, efficient way to type with your voice.

## Getting Started

### Prerequisites

- **Python 3.11+**
- **Git**

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/amalkp814/viapp
    cd viapp
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    # On Windows
    venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install the required packages:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the application:**
    ```bash
    python run.py
    ```
    The application will start in the system tray.

## Usage

1.  Press the activation hotkey (`F9` by default) to start recording.
2.  Speak clearly.
3.  The application will automatically detect the end of your speech, transcribe the audio, and type the text into the active window.

## Configuration

The application can be configured by editing the `src/config.yaml` file (created on the first run). You can change the activation hotkey, recording settings, and more. For a full list of options, see `src/config_schema.yaml`.

## License

This project is licensed under the GNU General Public License. See the [LICENSE](LICENSE) file for details.
