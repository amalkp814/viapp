import sounddevice as sd
from PyQt5.QtCore import QThread, pyqtSignal
from queue import Queue

from utils import ConfigManager


class AudioRecorder(QThread):
    """A dedicated thread for capturing audio from the microphone."""
    error = pyqtSignal(str)

    def __init__(self, audio_queue: Queue, parent=None):
        super().__init__(parent)
        self.audio_queue = audio_queue
        self.is_running = False
        self.stream = None

    def _audio_callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        if status:
            ConfigManager.console_print(f"Audio callback status: {status}")
        self.audio_queue.put(indata.copy())

    def run(self):
        """Main execution method for the thread."""
        self.is_running = True
        try:
            self.stream = self._get_audio_stream()
            with self.stream:
                while self.is_running:
                    self.msleep(100)
        except Exception as e:
            error_message = f"Error in AudioRecorder: {e}"
            ConfigManager.console_print(error_message)
            self.error.emit(error_message)
        finally:
            ConfigManager.console_print("AudioRecorder thread stopped.")

    def _get_audio_stream(self):
        recording_options = ConfigManager.get_config_section("recording_options")
        sample_rate = recording_options.get("sample_rate") or 16000
        frame_duration_ms = 30
        frame_size = int(sample_rate * (frame_duration_ms / 1000.0))

        device = recording_options.get("sound_device")
        # Ensure device is an integer if specified, otherwise use default
        if device is not None and device != "":
            try:
                device = int(device)
            except (ValueError, TypeError):
                ConfigManager.console_print(
                    f"Warning: Invalid 'sound_device' value '{device}' in config. Using default device."
                )
                device = None
        else:
            device = None

        try:
            # First attempt to open the stream with the specified or default device
            return sd.InputStream(
                samplerate=sample_rate,
                channels=1,
                dtype="int16",
                blocksize=frame_size,
                device=device,
                callback=self._audio_callback,
            )
        except sd.PortAudioError as e:
            ConfigManager.console_print("\n--- Audio Device Error ---")
            ConfigManager.console_print(
                "Could not open default audio device. This can happen if you don't have a default microphone set in your OS."
            )

            try:
                devices = sd.query_devices()
                input_devices = [
                    (i, d) for i, d in enumerate(devices) if d["max_input_channels"] > 0
                ]

                if not input_devices:
                    ConfigManager.console_print(
                        "\nFATAL: No audio input devices found on this system."
                    )
                    ConfigManager.console_print("--------------------------\n")
                    raise e

                fallback_device_index, fallback_device_info = input_devices[0]
                ConfigManager.console_print(
                    f"Attempting to use the first available microphone as a fallback: '{fallback_device_info['name']}' (Index: {fallback_device_index})"
                )
                ConfigManager.console_print(
                    "If this is not the microphone you want to use, please specify the correct 'sound_device' index in your settings."
                )
                ConfigManager.console_print("--------------------------\n")

                return sd.InputStream(
                    samplerate=sample_rate,
                    channels=1,
                    dtype="int16",
                    blocksize=frame_size,
                    device=fallback_device_index,
                    callback=self._audio_callback,
                )
            except Exception as fallback_e:
                ConfigManager.console_print(
                    f"\nFATAL: The fallback audio device also failed to open: {fallback_e}"
                )
                ConfigManager.console_print(
                    "Please ensure your audio devices are working correctly and are not in use by another application."
                )
                ConfigManager.console_print("--------------------------\n")
                raise e

    def stop(self):
        """Stops the audio recording thread."""
        if self.is_running:
            self.is_running = False
            self.wait()
