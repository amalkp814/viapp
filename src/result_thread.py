
# Standard library imports
import time  # For timing operations
import traceback  # For printing error stack traces

# Third-party library imports
import numpy as np  # For numerical operations and arrays
import sounddevice as sd  # For audio recording
import webrtcvad  # For voice activity detection (detecting speech)

# PyQt5 imports for threading and signals
from PyQt5.QtCore import QThread, QMutex, pyqtSignal

# Other useful imports
from collections import deque  # Double-ended queue for efficient buffer management
from threading import Event  # For thread synchronization

# Local module imports
from transcription import transcribe  # Function to transcribe audio
from utils import ConfigManager  # Configuration manager for app settings


class ResultThread(QThread):
    """
    A thread class for handling audio recording, transcription, and result processing.

    Signals:
        statusSignal: Emits the current status of the thread (e.g., 'recording', 'transcribing', 'idle')
        resultSignal: Emits the transcription result
    """

    statusSignal = pyqtSignal(str)
    resultSignal = pyqtSignal(str)

    def __init__(self, local_model=None):
        super().__init__()
        self.local_model = local_model
        self.is_recording = False
        self.is_running = True
        self.sample_rate = None
        self.mutex = QMutex()

    def stop_recording(self):
        self.mutex.lock()
        self.is_recording = False
        self.mutex.unlock()

    def stop(self):
        self.mutex.lock()
        self.is_running = False
        self.mutex.unlock()
        self.statusSignal.emit('idle')
        self.wait()

    def run(self):
        try:
            if not self.is_running:
                return

            self.mutex.lock()
            self.is_recording = True
            self.mutex.unlock()

            self.statusSignal.emit('recording')
            ConfigManager.console_print('Recording...')
            audio_data = self._record_audio()

            if not self.is_running:
                return

            if audio_data is None:
                self.statusSignal.emit('idle')
                return

            self.statusSignal.emit('transcribing')
            ConfigManager.console_print('Transcribing...')

            start_time = time.time()
            result = transcribe(audio_data, self.local_model)
            end_time = time.time()

            transcription_time = end_time - start_time
            ConfigManager.console_print(f'Transcription completed in {transcription_time:.2f} seconds. Post-processed line: {result}')

            if not self.is_running:
                return

            self.statusSignal.emit('idle')
            self.resultSignal.emit(result)

        except Exception:
            traceback.print_exc()
            self.statusSignal.emit('error')
            self.resultSignal.emit('')
        finally:
            self.stop_recording()

    def _record_audio(self):
        """
        Record audio from the microphone and return as a numpy int16 array.

        Returns None if recording is too short or considered noise.
        """
        # Get recording options from config (safely handle missing section)
        recording_options = ConfigManager.get_config_section('recording_options') or {}
        self.sample_rate = int(recording_options.get('sample_rate') or 16000)

        frame_duration_ms = 30
        frame_size = int(self.sample_rate * (frame_duration_ms / 1000.0))

        # Silence thresholds (ms) and convert to frame counts
        # `silence_duration` is legacy; prefer `min_silence_ms` for the actual stopping threshold
        silence_duration_ms = int(recording_options.get('silence_duration') or 900)
        # Increase default minimum silence to 800ms to reduce early chopping of soft speech
        min_silence_ms = int(recording_options.get('min_silence_ms') or 800)
        silence_frames = int(silence_duration_ms / frame_duration_ms)
        min_silence_frames = int(min_silence_ms / frame_duration_ms)

        # Skip first ~150ms worth of frames to avoid keypress noise
        initial_frames_to_skip = int(0.15 * self.sample_rate / frame_size)

        recording_mode = recording_options.get('recording_mode') or 'continuous'
        vad = None
        # Track whether VAD ever detected speech during the recording
        speech_detected = False
        if recording_mode in ('voice_activity_detection', 'continuous'):
            # Aggressiveness default 2; allow lowering via config
            vad_aggressiveness = int(recording_options.get('vad_aggressiveness') or 2)
            try:
                vad = webrtcvad.Vad(vad_aggressiveness)
            except Exception:
                vad = webrtcvad.Vad(2)
            silent_frame_count = 0
            # Track last time we observed voice activity (timestamp in seconds)
            last_voice_time = None
            # Smoothed per-frame RMS to reduce flicker (exponential moving average)
            rms_ema = 0.0
            rms_ema_alpha = float(recording_options.get('rms_ema_alpha') or 0.4)
            # Require N consecutive speech frames to consider speech started (helps ignore blips)
            consecutive_speech_required = int(recording_options.get('consecutive_speech_frames') or 2)
            consecutive_speech_count = 0

        audio_buffer = deque()
        recording = []

        data_ready = Event()

        def audio_callback(indata, frames, time_info, status):
            if status:
                ConfigManager.console_print(f"Audio callback status: {status}")
            # Ensure we append raw int16 samples
            try:
                samples = indata[:, 0].tolist()
            except Exception:
                samples = list(indata.flatten())
            audio_buffer.extend(samples)
            data_ready.set()

        # Start recording
        with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype='int16',
                            blocksize=frame_size, device=recording_options.get('sound_device'),
                            callback=audio_callback):
            # enforce a maximum recording duration (ms)
            max_recording_duration_ms = int(recording_options.get('max_recording_duration_ms') or 15000)
            start_record_time = time.time()

            while self.is_running and self.is_recording:
                data_ready.wait()
                data_ready.clear()

                if len(audio_buffer) < frame_size:
                    continue

                # Build a fixed-size frame from the buffer
                frame_samples = [audio_buffer.popleft() for _ in range(frame_size)]
                frame = np.array(frame_samples, dtype=np.int16)
                recording.extend(frame.tolist())

                if initial_frames_to_skip > 0:
                    initial_frames_to_skip -= 1
                    continue

                if vad:
                    # compute per-frame normalized RMS to help handle soft speech
                    try:
                        int16_max = float(np.iinfo(np.int16).max)
                    except Exception:
                        int16_max = 32768.0
                    try:
                        frame_rms = float(np.sqrt(np.mean(frame.astype(np.float32) ** 2)))
                        frame_rms_norm = frame_rms / int16_max
                    except Exception:
                        frame_rms_norm = 0.0

                    try:
                        vad_speech = vad.is_speech(frame.tobytes(), self.sample_rate)
                    except Exception:
                        vad_speech = False

                    # A frame is considered speech if VAD says so OR its energy exceeds a small threshold.
                    # This prevents VAD false-negatives from chopping soft speech.
                    energy_speech_threshold = recording_options.get('energy_speech_threshold_norm')
                    if energy_speech_threshold is None:
                        # default to something slightly above the noise threshold
                        energy_speech_threshold = max(0.01, (recording_options.get('noise_threshold_norm') or 0.02) * 1.2)
                    try:
                        energy_speech_threshold = float(energy_speech_threshold)
                    except Exception:
                        energy_speech_threshold = 0.01

                    is_speech = vad_speech or (frame_rms_norm >= energy_speech_threshold)

                    current_time = time.time()
                    # Update smoothed RMS
                    try:
                        rms_ema = (rms_ema_alpha * frame_rms_norm) + ((1.0 - rms_ema_alpha) * rms_ema)
                    except Exception:
                        rms_ema = frame_rms_norm

                    # Use smoothed RMS for energy-based speech decision to avoid frame-to-frame jitter
                    energy_based = (rms_ema >= energy_speech_threshold)
                    if vad_speech or energy_based:
                        silent_frame_count = 0
                        consecutive_speech_count += 1
                        last_voice_time = current_time
                        if not speech_detected and consecutive_speech_count >= consecutive_speech_required:
                            ConfigManager.console_print("Speech detected.")
                            speech_detected = True
                    else:
                        silent_frame_count += 1
                        consecutive_speech_count = 0

                    # Prefer timestamp-based silence: stop only if we've seen speech and
                    # the time since last detected speech exceeds the configured min_silence_ms.
                    if speech_detected and last_voice_time is not None:
                        ms_since_last_voice = (current_time - last_voice_time) * 1000.0
                        if ms_since_last_voice >= min_silence_ms:
                            ConfigManager.console_print(f"Silence duration {ms_since_last_voice:.0f}ms >= {min_silence_ms}ms; stopping.")
                            break

                # Check max duration and stop if exceeded
                elapsed_ms = (time.time() - start_record_time) * 1000.0
                if elapsed_ms >= max_recording_duration_ms:
                    ConfigManager.console_print(f'Max recording duration reached ({max_recording_duration_ms} ms). Stopping.')
                    break

        # Convert recorded samples to numpy array
        audio_data = np.array(recording, dtype=np.int16)
        duration = len(audio_data) / float(self.sample_rate) if self.sample_rate else 0.0

        ConfigManager.console_print(f'Recording finished. Size: {audio_data.size} samples, Duration: {duration:.2f} seconds')

        min_duration_ms = int(recording_options.get('min_duration') or 100)

        if (duration * 1000) < min_duration_ms:
            ConfigManager.console_print('Discarded due to being too short.')
            return None

        # Compute RMS energy and filter out noise-only recordings.
        # Use a normalized RMS (0.0 - 1.0) so thresholds are device-independent.
        try:
            rms = float(np.sqrt(np.mean(audio_data.astype(np.float32) ** 2)))
        except Exception:
            rms = 0.0

        # Normalized RMS (divide by int16 max). Use np.iinfo for correctness.
        try:
            int16_max = float(np.iinfo(np.int16).max)
        except Exception:
            int16_max = 32768.0

        try:
            rms_norm = rms / int16_max
        except Exception:
            rms_norm = 0.0

        # Support a normalized threshold in config (0.0 - 1.0). If absent, fall back to legacy
        # int16 threshold if provided, otherwise default to 0.02.
        noise_threshold_norm = recording_options.get('noise_threshold_norm')
        if noise_threshold_norm is None:
            legacy_thresh = recording_options.get('noise_threshold')
            if legacy_thresh is not None:
                try:
                    noise_threshold_norm = float(legacy_thresh) / int16_max
                except Exception:
                    noise_threshold_norm = 0.02
            else:
                noise_threshold_norm = 0.02
        else:
            try:
                noise_threshold_norm = float(noise_threshold_norm)
            except Exception:
                noise_threshold_norm = 0.02

        # Option: skip the noise-power discard if VAD detected speech during recording.
        skip_noise_check_if_speech = recording_options.get('skip_noise_check_if_speech')
        if skip_noise_check_if_speech is None:
            skip_noise_check_if_speech = True

        # If VAD detected speech and skipping is enabled, do not discard based on RMS.
        if speech_detected and skip_noise_check_if_speech:
            ConfigManager.console_print(f'VAD detected speech; skipping RMS noise check (rms_norm={rms_norm:.4f})')
        else:
            try:
                if rms_norm < float(noise_threshold_norm):
                    ConfigManager.console_print(f'Discarded due to low normalized RMS ({rms_norm:.4f} < {noise_threshold_norm}) - treated as noise')
                    return None
            except Exception:
                # If comparison fails for any reason, do not discard
                pass

        return audio_data
