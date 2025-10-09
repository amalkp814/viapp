
# Standard library imports
import time  # For timing operations
import traceback  # For printing error stack traces

# Third-party library imports
import numpy as np  # For numerical operations and arrays
import sounddevice as sd  # For audio recording
import tempfile  # For creating temporary files (not used here, but often for audio)
import wave  # For handling WAV audio files (not used here)
import webrtcvad  # For voice activity detection (detecting speech)

# PyQt5 imports for threading and signals
from PyQt5.QtCore import QThread, QMutex, pyqtSignal

# Other useful imports
from collections import deque  # Double-ended queue for efficient buffer management
from threading import Event  # For thread synchronization

# Local module imports
from transcription import transcribe  # Function to transcribe audio
from utils import ConfigManager  # Configuration manager for app settings



# This class runs in a separate thread to handle audio recording and transcription
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
    """


    # Signal to update the status (e.g., 'recording', 'transcribing', 'idle')
    statusSignal = pyqtSignal(str)
    # Signal to send the transcription result
    resultSignal = pyqtSignal(str)


    def __init__(self, local_model=None):
        """
        Initialize the ResultThread.

        :param local_model: Local transcription model (if applicable)
        """
        super().__init__()
        self.local_model = local_model  # Model used for transcription
        self.is_recording = False  # Flag to control recording state
        self.is_running = True  # Flag to control thread running state
        self.sample_rate = None  # Audio sample rate (Hz)
        self.mutex = QMutex()  # Mutex for thread-safe state changes


    def stop_recording(self):
        """
        Stop the current recording session.
        This sets the is_recording flag to False, which will stop the audio loop.
        """
        self.mutex.lock()
        self.is_recording = False
        self.mutex.unlock()


    def stop(self):
        """
        Stop the entire thread execution.
        This sets the is_running flag to False and waits for the thread to finish.
        """
        self.mutex.lock()
        self.is_running = False
        self.mutex.unlock()
        self.statusSignal.emit('idle')  # Notify UI that thread is idle
        self.wait()  # Wait for thread to finish


    def run(self):
        """
        Main execution method for the thread.
        This method is called when the thread starts. It handles recording and transcription.
        """
        try:
            # If thread is not running, exit
            if not self.is_running:
                return

            # Start recording
            self.mutex.lock()
            self.is_recording = True
            self.mutex.unlock()

            self.statusSignal.emit('recording')  # Notify UI
            ConfigManager.console_print('Recording...')
            audio_data = self._record_audio()  # Record audio from microphone

            # If thread was stopped during recording, exit
            if not self.is_running:
                return

            # If no audio was recorded (too short), go idle
            if audio_data is None:
                self.statusSignal.emit('idle')
                return

            # Transcribe the recorded audio
            self.statusSignal.emit('transcribing')
            ConfigManager.console_print('Transcribing...')

            # Time the transcription process
            start_time = time.time()
            result = transcribe(audio_data, self.local_model)
            end_time = time.time()

            transcription_time = end_time - start_time
            ConfigManager.console_print(f'Transcription completed in {transcription_time:.2f} seconds. Post-processed line: {result}')

            # If thread was stopped during transcription, exit
            if not self.is_running:
                return

            # Send result to UI and go idle
            self.statusSignal.emit('idle')
            self.resultSignal.emit(result)

        except Exception as e:
            # Print error stack trace and notify UI of error
            traceback.print_exc()
            self.statusSignal.emit('error')
            self.resultSignal.emit('')
        finally:
            # Always stop recording at the end
            self.stop_recording()


    def _record_audio(self):
        """
        Record audio from the microphone and save it to a numpy array.

        :return: numpy array of audio data, or None if the recording is too short
        """
        # Get recording options from config
        recording_options = ConfigManager.get_config_section('recording_options')
        self.sample_rate = recording_options.get('sample_rate') or 16000  # Default to 16kHz

        frame_duration_ms = 30  # Each audio frame is 30ms long (used for VAD)
        frame_size = int(self.sample_rate * (frame_duration_ms / 1000.0))  # Number of samples per frame

        silence_duration_ms = recording_options.get('silence_duration') or 900  # How long silence before stopping
        silence_frames = int(silence_duration_ms / frame_duration_ms)  # Number of silent frames before stopping

        # Skip first 150ms to avoid key press noise being detected as speech
        initial_frames_to_skip = int(0.15 * self.sample_rate / frame_size)

        # Choose recording mode (continuous or voice activity detection)
        recording_mode = recording_options.get('recording_mode') or 'continuous'
        vad = None
        if recording_mode in ('voice_activity_detection', 'continuous'):
            vad = webrtcvad.Vad(2)  # VAD aggressiveness: 0 (least) to 3 (most)
            speech_detected = False  # Flag for speech detection
            silent_frame_count = 0  # Counter for silent frames

        audio_buffer = deque(maxlen=frame_size)  # Buffer for incoming audio
        recording = []  # List to store all recorded samples

        data_ready = Event()  # Event to signal when new audio data is ready

        # This function is called whenever new audio data is available
        def audio_callback(indata, frames, time, status):
            if status:
                ConfigManager.console_print(f"Audio callback status: {status}")
            audio_buffer.extend(indata[:, 0])  # Add new samples to buffer
            data_ready.set()  # Signal that data is ready

        # Start recording from microphone
        with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype='int16',
                            blocksize=frame_size, device=recording_options.get('sound_device'),
                            callback=audio_callback):
            while self.is_running and self.is_recording:
                data_ready.wait()  # Wait for new audio data
                data_ready.clear()  # Reset event

                if len(audio_buffer) < frame_size:
                    continue  # Not enough data yet

                # Save current frame to recording
                frame = np.array(list(audio_buffer), dtype=np.int16)
                audio_buffer.clear()
                recording.extend(frame)

                # Skip initial frames to avoid false speech detection
                if initial_frames_to_skip > 0:
                    initial_frames_to_skip -= 1
                    continue

                # If using VAD, check for speech/silence
                if vad:
                    if vad.is_speech(frame.tobytes(), self.sample_rate):
                        silent_frame_count = 0  # Reset silence counter
                        if not speech_detected:
                            ConfigManager.console_print("Speech detected.")
                            speech_detected = True
                    else:
                        silent_frame_count += 1  # Increase silence counter

                    # If speech was detected and now enough silence, stop recording
                    if speech_detected and silent_frame_count > silence_frames:
                        break

        # Convert recorded samples to numpy array
        audio_data = np.array(recording, dtype=np.int16)
        duration = len(audio_data) / self.sample_rate  # Duration in seconds

        ConfigManager.console_print(f'Recording finished. Size: {audio_data.size} samples, Duration: {duration:.2f} seconds')

        min_duration_ms = recording_options.get('min_duration') or 100  # Minimum duration required

        # If recording is too short, discard it
        if (duration * 1000) < min_duration_ms:
            ConfigManager.console_print(f'Discarded due to being too short.')
            return None

        return audio_data  # Return the recorded audio as numpy array
