import time
import traceback
import sounddevice as sd
from PyQt5.QtCore import QThread, pyqtSignal
from multiprocessing import Process, Queue

from transcription import transcribe, create_local_model
from utils import ConfigManager


def transcription_process(audio_queue, result_queue, partial_result_queue):
    """
    A separate process dedicated to transcribing audio data.
    Initializes its own transcription model.
    """
    local_model = create_local_model()

    while True:
        try:
            audio_chunk = audio_queue.get()
            if audio_chunk is None:  # Sentinel value to stop the process
                break
            result = transcribe(audio_chunk, local_model)
            if result:
                partial_result_queue.put(result)
        except Exception as e:
            traceback.print_exc()
            continue


class ResultThread(QThread):
    """
    A thread class for handling audio recording and managing the transcription process.
    """

    statusSignal = pyqtSignal(str)
    resultSignal = pyqtSignal(str)
    partialResultSignal = pyqtSignal(str)

    def __init__(self):
        """
        Initialize the ResultThread.
        """
        super().__init__()
        self.is_running = False
        self.audio_queue = Queue()
        self.result_queue = Queue()
        self.partial_result_queue = Queue()
        self.transcription_process = None
        self.partial_result_monitor = None

    def stop(self):
        """Stop the entire thread execution and the transcription process."""
        self.is_running = False
        if self.partial_result_monitor:
            self.partial_result_monitor.stop()

        if self.transcription_process and self.transcription_process.is_alive():
            self.audio_queue.put(None)
            self.transcription_process.join(timeout=2)
            if self.transcription_process.is_alive():
                self.transcription_process.terminate()

    def run(self):
        """Main execution method for the thread."""
        try:
            self.statusSignal.emit("recording")
            ConfigManager.console_print("Recording...")
            self.is_running = True

            self.transcription_process = Process(
                target=transcription_process,
                args=(
                    self.audio_queue,
                    self.result_queue,
                    self.partial_result_queue,
                ),
            )
            self.transcription_process.start()

            self.start_partial_result_monitoring()
            self._audio_recorder()

            self.statusSignal.emit("idle")
            ConfigManager.console_print("Stopped.")

        except Exception as e:
            traceback.print_exc()
            self.statusSignal.emit("error")
        finally:
            self.resultSignal.emit("")

    def start_partial_result_monitoring(self):
        """Starts a QThread worker to monitor the partial result queue."""

        class PartialResultMonitor(QThread):
            def __init__(self, queue, signal):
                super().__init__()
                self.queue = queue
                self.signal = signal
                self.is_running = True

            def run(self):
                while self.is_running:
                    try:
                        result = self.queue.get(timeout=0.1)
                        if result:
                            self.signal.emit(result)
                    except Exception:
                        continue

            def stop(self):
                self.is_running = False

        self.partial_result_monitor = PartialResultMonitor(
            self.partial_result_queue, self.partialResultSignal
        )
        self.partial_result_monitor.start()

    def _audio_recorder(self):
        """
        Captures audio from the microphone and puts it into the queue.
        """
        recording_options = ConfigManager.get_config_section("recording_options")
        sample_rate = recording_options.get("sample_rate") or 16000
        frame_duration_ms = 100
        frame_size = int(sample_rate * (frame_duration_ms / 1000.0))

        try:
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
        except sd.PortAudioError as pae:
            ConfigManager.console_print(
                f"PortAudioError in InputStream: {pae}", "error"
            )
            self.statusSignal.emit("error")
        except Exception as e:
            ConfigManager.console_print(
                f"An unexpected error occurred in _audio_recorder: {e}", "error"
            )
            self.statusSignal.emit("error")

    def _audio_callback(self, indata, frames, time, status):
        """
        This callback is called by the sounddevice library for each audio chunk.
        """
        if status:
            ConfigManager.console_print(f"Audio callback status: {status}", "warning")
        if self.is_running:
            self.audio_queue.put(indata.copy())
