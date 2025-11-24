import time
import traceback
import numpy as np
import webrtcvad
from PyQt5.QtCore import QThread, pyqtSignal
from queue import Queue, Empty

from transcription import transcribe_local, post_process_transcription
from utils import ConfigManager


class TranscriptionProcessor(QThread):
    """
    A thread that processes audio from a queue, transcribes it, and emits the results.
    """

    statusSignal = pyqtSignal(str)
    resultSignal = pyqtSignal(str)
    partialResultSignal = pyqtSignal(str)

    def __init__(self, audio_queue: Queue, local_model):
        super().__init__()
        self.audio_queue = audio_queue
        self.local_model = local_model
        self.is_running = False

    def stop(self):
        """Stop the thread execution."""
        self.is_running = False

    def run(self):
        """Main execution method for the thread."""
        self.is_running = True
        ConfigManager.console_print("TranscriptionProcessor thread started.")
        self.statusSignal.emit("recording")

        try:
            for audio_chunk in self._process_audio_with_vad():
                if not self.is_running:
                    break

                self.statusSignal.emit("transcribing")

                transcription_generator = transcribe_local(audio_chunk, self.local_model)

                full_transcription = ""
                for segment in transcription_generator:
                    if not self.is_running:
                        break

                    full_transcription += segment
                    # Emit the live, un-post-processed text
                    self.partialResultSignal.emit(full_transcription)

                final_result = post_process_transcription(full_transcription)
                self.resultSignal.emit(final_result)

                # After processing a chunk, go back to 'recording' state
                # until the next speech is detected and transcribed.
                if self.is_running:
                    self.statusSignal.emit("recording")

        except Exception as e:
            traceback.print_exc()
            self.statusSignal.emit("error")
            self.resultSignal.emit("")
        finally:
            ConfigManager.console_print("TranscriptionProcessor thread stopped.")
            self.statusSignal.emit("idle")

    def _process_audio_with_vad(self):
        """
        Processes audio from the queue using VAD to yield speech chunks.
        """
        recording_options = ConfigManager.get_config_section("recording_options")
        sample_rate = recording_options.get("sample_rate") or 16000
        frame_duration_ms = 30
        silence_duration_ms = recording_options.get("silence_duration") or 900
        silence_frames = int(silence_duration_ms / frame_duration_ms)

        vad = webrtcvad.Vad(3)
        speech_detected = False
        silent_frame_count = 0
        recording = []

        while self.is_running:
            frame_data = None
            try:
                frame_data = self.audio_queue.get(timeout=0.1)
            except Empty:
                # If the queue is empty, we still need to process the VAD state
                pass

            if frame_data is not None:
                frame = np.frombuffer(frame_data, dtype=np.int16)
                is_speech = vad.is_speech(frame.tobytes(), sample_rate)

                if is_speech:
                    silent_frame_count = 0
                    if not speech_detected:
                        ConfigManager.console_print("Speech detected.")
                        speech_detected = True
                    recording.append(frame)
                elif speech_detected:
                    silent_frame_count += 1
            elif speech_detected:
                # If the queue is empty but we were in a speech segment,
                # increment the silence counter.
                silent_frame_count += 1

            if speech_detected and silent_frame_count > silence_frames:
                audio_data = np.concatenate(recording, axis=0)
                duration = len(audio_data) / sample_rate
                ConfigManager.console_print(
                    f"Chunk finished. Duration: {duration:.2f} seconds"
                )
                min_duration_ms = recording_options.get("min_duration") or 100
                if (duration * 1000) >= min_duration_ms:
                    yield audio_data

                recording = []
                speech_detected = False
                silent_frame_count = 0

        # Process any remaining audio in the buffer when stopping
        if recording:
            audio_data = np.concatenate(recording, axis=0)
            yield audio_data
