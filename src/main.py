import os
import sys
from queue import Queue
from PyQt5.QtCore import QObject, QProcess, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction, QMessageBox

from key_listener import KeyListener
from audio_recorder import AudioRecorder
from transcription_processor import TranscriptionProcessor
from ui.main_window import MainWindow
from ui.settings_window import SettingsWindow
from transcription import create_local_model
from input_simulation import InputSimulator
from utils import ConfigManager


class viappApp(QObject):
    stateChanged = pyqtSignal(str)

    def __init__(self):
        """
        Initialize the application, opening settings window if no configuration file is found.
        """
        super().__init__()
        self.app = QApplication(sys.argv)
        self.app.setWindowIcon(QIcon(os.path.join("assets", "v-logo.png")))

        ConfigManager.initialize()

        self.settings_window = SettingsWindow()
        self.settings_window.settings_closed.connect(self.on_settings_closed)
        self.settings_window.settings_saved.connect(self.restart_app)

        self.audio_queue = Queue()
        self.audio_recorder = None
        self.transcription_processor = None
        self.last_typed_text = ""

        if ConfigManager.config_file_exists():
            self.initialize_components()
        else:
            print("No valid configuration file found. Opening settings window...")
            self.settings_window.show()

    def initialize_components(self):
        """
        Initialize the components of the application.
        """
        self.input_simulator = InputSimulator()

        self.key_listener = KeyListener()
        self.key_listener.add_callback("on_activate", self.on_activation)
        self.key_listener.add_callback("on_deactivate", self.on_deactivation)
        self.key_listener.start()

        self.local_model = create_local_model()

        self.main_window = MainWindow()
        self.main_window.openSettings.connect(self.settings_window.show)
        self.main_window.startListening.connect(self.on_activation)
        self.main_window.stopListening.connect(self.on_activation)
        self.main_window.stopListeningAndDiscard.connect(self.stop_threads)
        self.main_window.closeApp.connect(self.exit_app)

        self.stateChanged.connect(self.main_window.set_state)
        self.stateChanged.connect(self.update_tray_menu)

        self.create_tray_icon()
        self.main_window.show()

    def create_tray_icon(self):
        """
        Create the system tray icon and its context menu.
        """
        self.tray_icon = QSystemTrayIcon(
            QIcon(os.path.join("assets", "v-logo.png")), self.app
        )
        self.tray_icon.show()
        self.update_tray_menu("idle")

    def update_tray_menu(self, state):
        """
        Update the system tray icon's context menu based on the application's state.
        """
        tray_menu = QMenu()

        show_action = QAction(QIcon(os.path.join("assets", "v-logo.png")), "viapp", self.app)
        show_action.triggered.connect(self.main_window.show)
        tray_menu.addAction(show_action)

        if state == "idle":
            start_action = QAction(QIcon(os.path.join("assets", "mic-rec.png")), "Start", self.app)
            start_action.triggered.connect(self.main_window.show)
            start_action.triggered.connect(self.on_activation)
            tray_menu.addAction(start_action)
        else:
            stop_action = QAction(QIcon(os.path.join("assets", "mic-idle.png")), "Stop", self.app)
            stop_action.triggered.connect(self.main_window.hide)
            stop_action.triggered.connect(self.on_activation)
            tray_menu.addAction(stop_action)

        settings_action = QAction(QIcon(os.path.join("assets", "gear.png")), "Settings", self.app)
        settings_action.triggered.connect(self.settings_window.show)
        tray_menu.addAction(settings_action)

        exit_action = QAction(QIcon(os.path.join("assets", "exit.png")), "Exit", self.app)
        exit_action.triggered.connect(self.exit_app)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)

    def cleanup(self):
        """
        Clean up resources before exiting or restarting.
        """
        if self.key_listener:
            self.key_listener.stop()
        if self.input_simulator:
            self.input_simulator.cleanup()
        self.stop_threads()

    def exit_app(self):
        """
        Exit the application.
        """
        self.cleanup()
        QApplication.quit()

    def restart_app(self):
        """Restart the application to apply the new settings."""
        self.cleanup()
        QApplication.quit()
        QProcess.startDetached(sys.executable, sys.argv)

    def on_settings_closed(self):
        """
        If settings is closed without saving on first run, initialize the components with default values.
        """
        if not os.path.exists(os.path.join("src", "config.yaml")):
            QMessageBox.information(
                self.settings_window,
                "Using Default Values",
                "Settings closed without saving. Default values are being used.",
            )
            self.initialize_components()

    def on_activation(self):
        """
        Called when the activation key combination is pressed. Toggles recording state.
        """
        is_running = self.audio_recorder and self.audio_recorder.isRunning()
        self.main_window.show()

        if is_running:
            recording_mode = ConfigManager.get_config_value("recording_options", "recording_mode")
            if recording_mode in ("press_to_toggle", "continuous"):
                self.stop_threads()
            return

        self.start_threads()

    def on_deactivation(self):
        """
        Called when the deactivation key combination is released (for hold-to-record mode).
        """
        if (
            ConfigManager.get_config_value("recording_options", "recording_mode")
            in ("hold_to_record",)
        ):
            self.stop_threads()

    def start_threads(self):
        """
        Start the audio recorder and transcription processor threads.
        """
        if self.audio_recorder and self.audio_recorder.isRunning():
            return

        self.audio_recorder = AudioRecorder(self.audio_queue)
        self.audio_recorder.start()

        self.transcription_processor = TranscriptionProcessor(self.audio_queue, self.local_model)
        self.transcription_processor.statusSignal.connect(self.on_status_update)
        self.transcription_processor.resultSignal.connect(self.on_transcription_complete)
        self.transcription_processor.partialResultSignal.connect(self.on_partial_transcription)
        self.transcription_processor.start()

        self.stateChanged.emit("recording")

    def stop_threads(self):
        """
        Stop the audio recorder and transcription processor threads.
        """
        if self.audio_recorder:
            self.audio_recorder.stop()
            self.audio_recorder = None

        if self.transcription_processor:
            self.transcription_processor.stop()
            self.transcription_processor = None

        # Clear the queue
        while not self.audio_queue.empty():
            self.audio_queue.get()

        self.last_typed_text = ""
        self.stateChanged.emit("idle")


    def on_status_update(self, status):
        """
        Update the main window's state.
        """
        self.stateChanged.emit(status)

    def on_partial_transcription(self, result):
        """
        When a partial transcription is available, update the main window and type the result.
        """
        self.main_window.update_transcription_label(result)

        # Live typing logic
        if self.last_typed_text in result:
            # Append new characters
            diff = result[len(self.last_typed_text):]
            self.input_simulator.typewrite(diff)
        else:
            # Text has been corrected, backspace and re-type
            self.input_simulator.backspace(len(self.last_typed_text))
            self.input_simulator.typewrite(result)

        self.last_typed_text = result


    def on_transcription_complete(self, result):
        """
        When the transcription is complete, handle finalization tasks.
        """
        # The final result is processed here.
        # Since we are live-typing, the final text is already on the screen.
        # We might want to add a final space or punctuation.
        if (
            ConfigManager.get_config_section("post_processing")["add_trailing_space"]
            and self.last_typed_text
            and not self.last_typed_text.endswith(" ")
        ):
            self.input_simulator.typewrite(" ")

        if (
            ConfigManager.get_config_value("recording_options", "recording_mode")
            == "continuous"
        ):
            # In continuous mode, we don't stop, just reset the text
            self.last_typed_text = ""
        else:
            # For other modes, we are done now
            self.stateChanged.emit("idle")
            self.main_window.update_transcription_label("")

    def run(self):
        """
        Start the application.
        """
        sys.exit(self.app.exec_())


if __name__ == "__main__":
    app = viappApp()
    app.run()
