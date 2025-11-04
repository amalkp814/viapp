import time
import traceback
import numpy as np
import sounddevice as sd
import webrtcvad
from PyQt5.QtCore import QThread, pyqtSignal
from multiprocessing import Process, Queue

from transcription import transcribe, create_local_model
from utils import ConfigManager


def transcription_process(audio_queue, result_queue, partial_result_queue):
    """
    A separate process dedicated to transcribing audio data.
    Initializes its own configuration and transcription model.
    """
    ConfigManager.initialize()
    local_model = create_local_model()

    while True:
        try:
            audio_chunk = audio_queue.get()
            if audio_chunk is None:
                break
            result = transcribe(audio_chunk, local_model)
            if result:
                partial_result_queue.put(result)
        except Exception as e:
            traceback.print_exc()
            continue


class ResultThread(QThread):
    statusSignal = pyqtSignal(str)
    resultSignal = pyqtSignal(str)
    partialResultSignal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.is_running = False
        self.audio_queue = Queue()
        self.result_queue = Queue()
        self.partial_result_queue = Queue()
        self.transcription_process = None
        self.partial_result_monitor = None
        self.audio_stream = None

    def stop(self):
        self.is_running = False
        if self.audio_stream:
            self.audio_stream.stop()
            self.audio_stream.close()
        if self.partial_result_monitor:
            self.partial_result_monitor.stop()

        if self.transcription_process and self.transcription_process.is_alive():
            self.audio_queue.put(None)
            self.transcription_process.join(timeout=2)
            if self.transcription_process.is_alive():
                self.transcription_process.terminate()
        self.wait()

    def run(self):
        try:
            self.is_running = True
            self.statusSignal.emit("recording")
            ConfigManager.console_print("Recording...")

            self.transcription_process = Process(
                target=transcription_process,
                args=(self.audio_queue, self.result_queue, self.partial_result_queue),
            )
            self.transcription_process.start()
            self.start_partial_result_monitoring()

            self._process_audio()

        except Exception as e:
            traceback.print_exc()
            self.statusSignal.emit("error")
        finally:
            self.resultSignal.emit("")
            self.statusSignal.emit("idle")
            ConfigManager.console_print("Stopped.")

    def start_partial_result_monitoring(self):
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

    def _process_audio(self):
        recording_options = ConfigManager.get_config_section("recording_options")
        sample_rate = recording_options.get("sample_rate") or 16000
        frame_duration_ms = 30
        frame_size = int(sample_rate * (frame_duration_ms / 1000.0))
        silence_duration_ms = recording_options.get("silence_duration") or 900
        silence_frames = int(silence_duration_ms / frame_duration_ms)

        vad = webrtcvad.Vad(3)
        speech_detected = False
        silent_frame_count = 0
        recording = []

        raw_audio_queue = Queue()

        def audio_callback(indata, frames, time, status):
            if status:
                ConfigManager.console_print(f"Audio callback status: {status}", "warning")
            if self.is_running:
                raw_audio_queue.put(indata.copy())

        self.audio_stream = sd.InputStream(
            samplerate=sample_rate,
            channels=1,
            dtype="int16",
            blocksize=frame_size,
            device=recording_options.get("sound_device"),
            callback=audio_callback,
        )
        self.audio_stream.start()

        while self.is_running:
            try:
                frame_data = raw_audio_queue.get(timeout=0.1)
                frame = np.frombuffer(frame_data, dtype=np.int16)
                is_speech = vad.is_speech(frame.tobytes(), sample_rate)

                if is_speech:
                    silent_frame_count = 0
                    if not speech_detected:
                        speech_detected = True
                    recording.extend(frame)
                elif speech_detected:
                    silent_frame_count += 1

                if speech_detected and silent_frame_count > silence_frames:
                    audio_data = np.array(recording, dtype=np.int16)
                    self.audio_queue.put(audio_data)
                    recording = []
                    speech_detected = False
            except Exception:
                continue

        if recording:
            self.audio_queue.put(np.array(recording, dtype=np.int16))
