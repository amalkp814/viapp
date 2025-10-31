
import traceback
from PyQt5.QtCore import QThread, pyqtSignal
from transcription import transcribe
import soundfile as sf

class BatchThread(QThread):
    statusSignal = pyqtSignal(str)
    resultSignal = pyqtSignal(str)

    def __init__(self, filepaths, local_model=None):
        super().__init__()
        self.filepaths = filepaths
        self.local_model = local_model
        self.is_running = True

    def stop(self):
        self.is_running = False
        self.wait()

    def run(self):
        try:
            for filepath in self.filepaths:
                if not self.is_running:
                    break
                self.statusSignal.emit(f"Processing {filepath}...")
                audio_data = self.read_audio(filepath)
                if audio_data is not None:
                    result = transcribe(audio_data, self.local_model)
                    self.resultSignal.emit(result)
            self.statusSignal.emit("Batch processing complete.")
        except Exception:
            traceback.print_exc()
            self.statusSignal.emit("Error during batch processing.")

    def read_audio(self, filepath):
        try:
            audio_data, _ = sf.read(filepath, dtype='int16')
            return audio_data
        except Exception:
            traceback.print_exc()
            return None
