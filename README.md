
# viapp

![version](https://img.shields.io/badge/version-1.0.1-blue)

![demo](./assets/ww-demo-image-02.gif)

**Update (2024-05-28):** Major rewrite merged! We've migrated from using `tkinter` to `PyQt5` for the UI, added a new settings window for configuration, a continuous recording mode, and support for local APIs. If you encounter any problems, please [open an issue](https://github.com/amalkp814/viapp/issues).

viapp is a small speech-to-text app that uses [OpenAI's Whisper model](https://openai.com/research/whisper) to auto-transcribe recordings from your microphone to the active window.

When running, the app waits for a keyboard shortcut (default `ctrl+shift+space`). Press it to start recording. Recording modes:

- `continuous` (default): stop after a pause, transcribe, then restart until stopped.

- `voice_activity_detection`: record while speech is detected; stop after a pause.

- `press_to_toggle`: toggle recording with the activation key.

- `hold_to_record`: record while holding the activation key.

You can change the keyboard shortcut (`activation_key`) and recording mode in Configuration Options below. While recording, a small status area shows the current stage (can be hidden). When transcription completes, the text is typed to the active window.

Transcription can be local (`faster-whisper`) or via OpenAI's API. By default the app uses a local model; provide an API key or change base URL to use an API-based backend.

## Getting Started

### Prerequisites
Before you can run this app, you'll need to have the following software installed:

- Git: [https://git-scm.com/downloads](https://git-scm.com/downloads)
- Python `3.11`: [https://www.python.org/downloads/](https://www.python.org/downloads/)

If you want to run `faster-whisper` on your GPU, you'll also need to install the following NVIDIA libraries:

- [cuBLAS for CUDA 12](https://developer.nvidia.com/cublas)
- [cuDNN 8 for CUDA 12](https://developer.nvidia.com/cudnn)

### More information on GPU execution

The following notes are taken from the `faster-whisper` README:

- Note: the latest versions of `ctranslate2` target CUDA 12. For CUDA 11 you may need to pin to an older `ctranslate2` release.

- Use Docker images such as `nvidia/cuda:12.0.0-runtime-ubuntu20.04` or `nvidia/cuda:12.0.0-runtime-ubuntu22.04` which include the required libraries.

- On Linux you can install Python wrappers via pip and set `LD_LIBRARY_PATH` accordingly. Example:

```bash
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12

export LD_LIBRARY_PATH="$(python3 -c 'import os, nvidia.cublas.lib as cb, nvidia.cudnn.lib as cd; print(os.path.dirname(cb.__file__) + ":" + os.path.dirname(cd.__file__))')"
```

Ensure you pick package versions compatible with your CUDA/cuDNN stack.

### Installation
To set up and run the project, follow these steps:

#### 1. Clone the repository

```bash
git clone https://github.com/amalkp814/viapp
cd viapp
```bash

#### 2. Create a virtual environment and activate it

```bash
python -m venv venv

# For Linux and macOS:
source venv/bin/activate

# For Windows:
venv\Scripts\activate
```bash

#### 3. Install the required packages

```bash
# Install all required Python packages listed in requirements.txt
# Run this command inside your virtual environment (see previous step).
# This ensures your project has all the dependencies it needs to run.
pip install -r requirements.txt
```bash

#### 4. Run the Python code

```bash
python run.py
```


#### 5. Configure and start viapp
On first run, a Settings window should appear. Once configured and saved, another window will open. Press "Start" to activate the keyboard listener. Press the activation key (`ctrl+shift+space` by default) to start recording and transcribing to the active window.

### Configuration Options


viapp uses a configuration file to customize its behaviour. To set up the configuration, open the Settings window:

![settings demo](./assets/ww-settings-demo.gif)

#### Model Options

- `use_api`: Toggle to choose whether to use the OpenAI API or a local Whisper model for transcription. (Default: `false`)

- `common`: Options common to both API and local models.

  - `language`: The language code for the transcription in [ISO-639-1 format](https://en.wikipedia.org/wiki/List_of_ISO_639_language_codes). (Default: `null`)

  - `temperature`: Controls the randomness of the transcription output. Lower values make the output more focused and deterministic. (Default: `0.0`)

  - `initial_prompt`: A string used as an initial prompt to condition the transcription. (Default: `null`)

- `api`: Configuration options for the OpenAI API. See the [OpenAI API documentation](https://platform.openai.com/docs/api-reference/audio/create?lang=python) for more information.
  - `model`: The model to use for transcription. Currently, only `whisper-1` is available. (Default: `whisper-1`)
  - `base_url`: The base URL for the API. Can be changed to use a local API endpoint, such as [LocalAI](https://localai.io/). (Default: `https://api.openai.com/v1`)
  - `api_key`: Your API key for the OpenAI API. Required for non-local API usage. (Default: `null`)

- `local`: Configuration options for the local Whisper model.
  - `model`: The model to use for transcription. The larger models provide better accuracy but are slower. See [available models and languages](https://github.com/openai/whisper?tab=readme-ov-file#available-models-and-languages). (Default: `base`)
  - `device`: The device to run the local Whisper model on. Use `cuda` for NVIDIA GPUs, `cpu` for CPU-only processing, or `auto` to let the system automatically choose the best available device. (Default: `auto`)
  - `compute_type`: The compute type to use for the local Whisper model. [More information on quantization here](https://opennmt.net/CTranslate2/quantization.html). (Default: `default`)
  - `condition_on_previous_text`: Set to `true` to use the previously transcribed text as a prompt for the next transcription request. (Default: `true`)
  - `vad_filter`: Set to `true` to use [a voice activity detection (VAD) filter](https://github.com/snakers4/silero-vad) to remove silence from the recording. (Default: `false`)
  - `model_path`: The path to the local Whisper model. If not specified, the default model will be downloaded. (Default: `null`)

#### Recording Options
- `activation_key`: The keyboard shortcut to activate the recording and transcribing process. Separate keys with a `+`. (Default: `ctrl+shift+space`)
- `input_backend`: The input backend to use for detecting key presses. `auto` will try to use the best available backend. (Default: `auto`)
- `recording_mode`: The recording mode to use. Options include `continuous` (auto-restart recording after pause in speech until activation key is pressed again), `voice_activity_detection` (stop recording after pause in speech), `press_to_toggle` (stop recording when activation key is pressed again), `hold_to_record` (stop recording when activation key is released). (Default: `continuous`)
- `sound_device`: The numeric index of the sound device to use for recording. To find device numbers, run `python -m sounddevice`. (Default: `null`)
- `sample_rate`: The sample rate in Hz to use for recording. (Default: `16000`)
- `silence_duration`: The duration in milliseconds to wait for silence before stopping the recording. (Default: `900`)
- `min_duration`: The minimum duration in milliseconds for a recording to be processed. Recordings shorter than this will be discarded. (Default: `100`)
- `max_recording_duration_ms`: Maximum recording duration in milliseconds. Recording will stop automatically after this duration (default: 15000)
- `noise_threshold_norm`: Normalized energy threshold (0.0 - 1.0) used to detect noise-only recordings. Default: 0.02

#### Post-processing Options
- `writing_key_press_delay`: The delay in seconds between each key press when writing the transcribed text. (Default: `0.005`)
- `remove_trailing_period`: Set to `true` to remove the trailing period from the transcribed text. (Default: `false`)
- `add_trailing_space`: Set to `true` to add a space to the end of the transcribed text. (Default: `true`)
- `remove_capitalization`: Set to `true` to convert the transcribed text to lowercase. (Default: `false`)
- `input_method`: The method to use for simulating keyboard input. (Default: `pynput`)

#### Miscellaneous Options
- `print_to_terminal`: Set to `true` to print the script status and transcribed text to the terminal. (Default: `true`)
- `hide_status_window`: Set to `true` to hide the status window during operation. (Default: `false`)
- `noise_on_completion`: Set to `true` to play a noise after the transcription has been typed out. (Default: `false`)

If any of the configuration options are invalid or not provided, the program will use the default values.

## Known Issues

You can see all reported issues and their current status in our [Issue Tracker](https://github.com/savbell/whisper-writer/issues). If you encounter a problem, please [open a new issue](https://github.com/savbell/whisper-writer/issues/new) with a detailed description and reproduction steps, if possible.

## Roadmap
Below are features I am planning to add in the near future:
- [x] Restructuring configuration options to reduce redundancy
- [x] Update to use the latest version of the OpenAI API
- [ ] Additional post-processing options:
  - [ ] Simple word replacement (e.g. "gonna" -> "going to" or "smiley face" -> "😊")
  - [ ] Using GPT for instructional post-processing
- [x] Updating GUI
- [ ] Creating standalone executable file

Below are features not currently planned:
- [ ] Pipelining audio files


Implemented features can be found in the [CHANGELOG](CHANGELOG.md).

## Contributing

Contributions are welcome. Please open a pull request or create an issue on GitHub.

## Forking and Renaming viapp

To fork and rename the project:

1. Fork the repository on GitHub: [viapp](https://github.com/amalkp814/viapp)
2. Clone your fork locally and update references and metadata.
3. Rename files and update README/CHANGELOG as needed, then push to your fork.

## Credits

- [OpenAI](https://openai.com/) for the Whisper model and ChatGPT.
- [Guillaume Klein](https://github.com/guillaumekln) for the `faster-whisper` project.

## License

This project is licensed under the GNU General Public License. See the [LICENSE](LICENSE) file for details.
