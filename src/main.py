import os
import sys
import multiprocessing
from PyQt5.QtCore import QObject, QProcess, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction, QMessageBox

from key_listener import KeyListener
from result_thread import ResultThread
from ui.main_window import MainWindow
from ui.settings_window import SettingsWindow
from input_simulation import InputSimulator
from utils import ConfigManager


class viappApp(QObject):
    stateChanged = pyqtSignal(str)

    def __init__(self):
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
        self.input_simulator = InputSimulator()
        self.key_listener = KeyListener()
        self.key_listener.add_callback("on_activate", self.toggle_recording)
        self.result_thread = None
        self.main_window = MainWindow()
        self.main_window.openSettings.connect(self.settings_window.show)
        self.main_window.startListening.connect(self.toggle_recording)
        self.main_window.stopListening.connect(self.toggle_recording)
        self.main_window.closeApp.connect(self.exit_app)
        self.stateChanged.connect(self.main_window.set_state)
        self.create_tray_icon()
        self.main_window.show()

    def create_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(
            QIcon(os.path.join("assets", "v-logo.png")), self.app
        )
        tray_menu = QMenu()
        show_action = QAction("viapp Main Menu", self.app)
        show_action.triggered.connect(self.main_window.show)
        tray_menu.addAction(show_action)
        settings_action = QAction("Open Settings", self.app)
        settings_action.triggered.connect(self.settings_window.show)
        tray_menu.addAction(settings_action)
        exit_action = QAction("Exit", self.app)
        exit_action.triggered.connect(self.exit_app)
        tray_menu.addAction(exit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def cleanup(self):
        if self.result_thread and self.result_thread.isRunning():
            self.stop_result_thread()
        if self.key_listener:
            self.key_listener.stop()
        if self.input_simulator:
            self.input_simulator.cleanup()

    def exit_app(self):
        self.cleanup()
        QApplication.quit()

    def restart_app(self):
        self.cleanup()
        QApplication.quit()
        QProcess.startDetached(sys.executable, sys.argv)

    def on_settings_closed(self):
        if not os.path.exists(os.path.join("src", "config.yaml")):
            QMessageBox.information(
                self.settings_window,
                "Using Default Values",
                "Settings closed without saving. Default values are being used.",
            )
            self.initialize_components()

    def toggle_recording(self):
        if self.result_thread and self.result_thread.isRunning():
            self.stop_result_thread()
        else:
            self.start_result_thread()

    def start_result_thread(self):
        if self.result_thread and self.result_thread.isRunning():
            return
        self.result_thread = ResultThread()
        self.result_thread.statusSignal.connect(self.on_status_update)
        self.result_thread.resultSignal.connect(self.on_transcription_complete)
        self.result_thread.partialResultSignal.connect(
            self.on_partial_transcription
        )
        self.result_thread.start()

    def stop_result_thread(self):
        if self.result_thread and self.result_thread.isRunning():
            self.result_thread.stop()

    def on_status_update(self, status):
        self.stateChanged.emit(status)

    def on_partial_transcription(self, result):
        self.main_window.update_transcription_label(result)

    def on_transcription_complete(self, result):
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
        sys.exit(self.app.exec_())


if __name__ == "__main__":
    multiprocessing.freeze_support()
    app = viappApp()
    app.run()
