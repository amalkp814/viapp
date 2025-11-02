import time
import traceback
import numpy as np
import sounddevice as sd
import webrtcvad
from PyQt5.QtCore import QThread, QMutex, pyqtSignal
from queue import Queue

from transcription import transcribe
from utils import ConfigManager


class ResultThread(QThread):
    """
    A thread class for handling audio recording, transcription, and result processing.

    This class manages the entire process of:
    1. Recording audio from the microphone
    2. Detecting speech and silence
    3. Saving the recorded audio as numpy array
    4. Transcribing the audio
    5. Emitting the transcription result

    Signals:
        statusSignal: Emits the current status of the thread (e.g., 'recording', 'transcribing', 'idle')
        resultSignal: Emits the transcription result
        partialResultSignal: Emits partial transcription results
    """

    statusSignal = pyqtSignal(str)
    resultSignal = pyqtSignal(str)
    partialResultSignal = pyqtSignal(str)

    def __init__(self, local_model=None):
        """
        Initialize the ResultThread.

        :param local_model: Local transcription model (if applicable)
        """
        super().__init__()
        self.local_model = local_model
        self.is_recording = False
        self.is_running = True
        self.sample_rate = None
        self.mutex = QMutex()
        self.audio_queue = Queue()

    def stop_recording(self):
        """Stop the current recording session."""
        self.mutex.lock()
        self.is_recording = False
        self.mutex.unlock()

    def stop(self):
        """Stop the entire thread execution."""
        self.mutex.lock()
        self.is_running = False
        self.mutex.unlock()
        self.statusSignal.emit('idle')
        self.wait()

    def run(self):
        """Main execution method for the thread."""
        try:
            if not self.is_running:
                return

            self.mutex.lock()
            self.is_recording = True
            self.mutex.unlock()

            self.statusSignal.emit('recording')
            ConfigManager.console_print('Recording...')

            with self._get_audio_stream():
                for audio_chunk in self._process_audio_queue():
                    if not self.is_running:
                        break

                    self.statusSignal.emit('transcribing')
                    ConfigManager.console_print('Transcribing...')

                    # Time the transcription process
                    start_time = time.time()
                    result = transcribe(audio_chunk, self.local_model)
                    end_time = time.time()

                    transcription_time = end_time - start_time
                    ConfigManager.console_print(f'Transcription completed in {transcription_time:.2f} seconds. Post-processed line: {result}')

                    if not self.is_running:
                        break

                    self.partialResultSignal.emit(result)
                    self.resultSignal.emit(result)

            self.statusSignal.emit('idle')

        except Exception as e:
            traceback.print_exc()
            self.statusSignal.emit('error')
            self.resultSignal.emit('')
        finally:
            self.stop_recording()

    def _audio_callback(self, indata, frames, time, status):
        if status:
            ConfigManager.console_print(f"Audio callback status: {status}")
        self.audio_queue.put(indata.copy())

    def _get_audio_stream(self):
        recording_options = ConfigManager.get_config_section('recording_options')
        self.sample_rate = recording_options.get('sample_rate') or 16000
        frame_duration_ms = 30
        frame_size = int(self.sample_rate * (frame_duration_ms / 1000.0))

        return sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype='int16',
            blocksize=frame_size,
            device=recording_options.get('sound_device'),
            callback=self._audio_callback
        )

    def _process_audio_queue(self):
        recording_options = ConfigManager.get_config_section('recording_options')
        self.sample_rate = recording_options.get('sample_rate') or 16000
        frame_duration_ms = 30
        frame_size = int(self.sample_rate * (frame_duration_ms / 1000.0))
        silence_duration_ms = recording_options.get('silence_duration') or 900
        silence_frames = int(silence_duration_ms / frame_duration_ms)
        initial_frames_to_skip = int(0.15 * self.sample_rate / frame_size)

        vad = webrtcvad.Vad(3)
        speech_detected = False
        silent_frame_count = 0
        recording = []

        while self.is_running and self.is_recording:
            try:
                frame_data = self.audio_queue.get(timeout=1.0)
                frame = np.frombuffer(frame_data, dtype=np.int16)

                is_speech = vad.is_speech(frame.tobytes(), self.sample_rate)

                if is_speech:
                    silent_frame_count = 0
                    if not speech_detected:
                        ConfigManager.console_print("Speech detected.")
                        speech_detected = True
                    recording.extend(frame)
                elif speech_detected:
                    silent_frame_count += 1

                if speech_detected and silent_frame_count > silence_frames:
                    audio_data = np.array(recording, dtype=np.int16)
                    duration = len(audio_data) / self.sample_rate
                    ConfigManager.console_print(f'Chunk finished. Size: {audio_data.size} samples, Duration: {duration:.2f} seconds')
                    min_duration_ms = recording_options.get('min_duration') or 100
                    if (duration * 1000) >= min_duration_ms:
                        yield audio_data
                    recording = []
                    speech_detected = False
            except Exception as e:
                continue

        if recording:
            audio_data = np.array(recording, dtype=np.int16)
            duration = len(audio_data) / self.sample_rate
            ConfigManager.console_print(f'Final chunk finished. Size: {audio_data.size} samples, Duration: {duration:.2f} seconds')
            min_duration_ms = recording_options.get('min_duration') or 100
            if (duration * 1000) >= min_duration_ms:
                yield audio_data
