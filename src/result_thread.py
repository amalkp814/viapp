import time
import traceback
import numpy as np
import sounddevice as sd
from PyQt5.QtCore import QThread, pyqtSignal
from queue import Queue
import threading

from transcription import transcribe
from utils import ConfigManager


class ResultThread(QThread):
    """
    A thread class for handling audio recording, transcription, and result processing.
    """

    statusSignal = pyqtSignal(str)
    resultSignal = pyqtSignal(str)
    partialResultSignal = pyqtSignal(str)

    def __init__(self, local_model=None):
        """
        Initialize the ResultThread.
        """
        super().__init__()
        self.local_model = local_model
        self.is_running = True
        self.audio_queue = Queue()

    def stop(self):
        """Stop the entire thread execution."""
        self.is_running = False

    def run(self):
        """Main execution method for the thread."""
        try:
            self.statusSignal.emit("recording")
            ConfigManager.console_print("Recording...")

            audio_thread = threading.Thread(target=self._audio_recorder)
            audio_thread.start()

            transcription_thread = threading.Thread(target=self._transcribe_audio_queue)
            transcription_thread.start()

            while self.is_running:
                time.sleep(0.1)

            audio_thread.join()
            transcription_thread.join()

            self.statusSignal.emit("idle")

        except Exception as e:
            traceback.print_exc()
            self.statusSignal.emit("error")
            self.resultSignal.emit("")

    def _audio_recorder(self):
        """
        A dedicated thread for capturing audio from the microphone.
        """
        recording_options = ConfigManager.get_config_section("recording_options")
        sample_rate = recording_options.get("sample_rate") or 16000
        frame_duration_ms = 100
        frame_size = int(sample_rate * (frame_duration_ms / 1000.0))

        with sd.InputStream(
            samplerate=sample_rate,
            channels=1,
            dtype="int16",
            blocksize=frame_size,
            device=recording_options.get("sound_device"),
            callback=self._audio_callback,
        ):
            while self.is_running:
                time.sleep(0.1)

    def _audio_callback(self, indata, frames, time, status):
        if status:
            ConfigManager.console_print(f"Audio callback status: {status}")
        self.audio_queue.put(indata.copy())

    def _transcribe_audio_queue(self):
        """
        A dedicated thread for transcribing audio from the queue.
        """
        while self.is_running:
            try:
                audio_chunk = self.audio_queue.get(timeout=1.0)
                result = transcribe(audio_chunk, self.local_model)
                if result:
                    self.partialResultSignal.emit(result)
            except Exception as e:
                continue
