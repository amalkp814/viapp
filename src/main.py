import os
import sys
from PyQt5.QtCore import QObject, QProcess, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction, QMessageBox

from key_listener import KeyListener
from result_thread import ResultThread
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
        self.key_listener.add_callback("on_activate", self.toggle_recording)
        self.key_listener.add_callback("on_deactivate", self.on_deactivation)
        self.key_listener.start()

        self.result_thread = None

        self.main_window = MainWindow()
        self.main_window.openSettings.connect(self.settings_window.show)
        self.main_window.startListening.connect(self.toggle_recording)
        self.main_window.stopListening.connect(self.toggle_recording)
        self.main_window.stopListeningAndDiscard.connect(self.stop_result_thread)
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

        show_action = QAction("viapp Main Menu", self.app)
        show_action.triggered.connect(self.main_window.show)
        tray_menu.addAction(show_action)

        if state == "idle":
            start_action = QAction("Start Recording", self.app)
            start_action.triggered.connect(self.toggle_recording)
            tray_menu.addAction(start_action)
        else:
            stop_action = QAction("Stop Recording", self.app)
            stop_action.triggered.connect(self.toggle_recording)
            tray_menu.addAction(stop_action)

        settings_action = QAction("Settings", self.app)
        settings_action.triggered.connect(self.settings_window.show)
        tray_menu.addAction(settings_action)

        exit_action = QAction("Exit", self.app)
        exit_action.triggered.connect(self.exit_app)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)

    def cleanup(self):
        if self.result_thread and self.result_thread.isRunning():
            self.stop_result_thread()
        if self.key_listener:
            self.key_listener.stop()
        if self.input_simulator:
            self.input_simulator.cleanup()

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

    def toggle_recording(self):
        """
        Toggle the recording state.
        """
        if self.result_thread and self.result_thread.isRunning():
            self.stop_result_thread()
        else:
            self.start_result_thread()

    def on_deactivation(self):
        """
        Called when the activation key combination is released.
        """
        if (
            ConfigManager.get_config_value("recording_options", "recording_mode")
            in ("hold_to_record",)
        ):
            self.stop_result_thread()

    def start_result_thread(self):
        """
        Start the result thread to record audio and transcribe it.
        """
        if self.result_thread and self.result_thread.isRunning():
            return

        self.result_thread = ResultThread()
        self.result_thread.statusSignal.connect(self.on_status_update)
        self.result_thread.resultSignal.connect(self.on_transcription_complete)
        self.result_thread.partialResultSignal.connect(self.on_partial_transcription)
        self.result_thread.start()

    def stop_result_thread(self):
        """
        Stop the result thread.
        """
        if self.result_thread and self.result_thread.isRunning():
            self.result_thread.stop()

    def on_status_update(self, status):
        """
        Update the main window's state.
        """
        self.stateChanged.emit(status)

    def on_partial_transcription(self, result):
        """
        When a partial transcription is available, update the main window.
        """
        self.main_window.update_transcription_label(result)

    def on_transcription_complete(self, result):
        """
        When the transcription is complete, type the result and start listening for the activation key again.
        """
        self.input_simulator.typewrite(result)

        if (
            ConfigManager.get_config_value("recording_options", "recording_mode")
            == "continuous"
        ):
            self.start_result_thread()
        else:
            self.stateChanged.emit("idle")
            self.main_window.update_transcription_label("")

    def run(self):
        """
        Start the application.
        """
        sys.exit(self.app.exec_())


if __name__ == "__main__":
    import multiprocessing

    multiprocessing.freeze_support()
    app = viappApp()
    app.run()
