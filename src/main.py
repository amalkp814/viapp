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
    """
    Main application class for viapp.
    Manages the application lifecycle, GUI components, and core logic integration.
    """
    stateChanged = pyqtSignal(str)  # Signal to notify state changes (e.g., 'idle', 'recording', 'transcribing')

    def __init__(self):
        """
        Initialize the application, opening settings window if no configuration file is found.
        Sets up the main application instance, icon, and configuration manager.
        """
        super().__init__()
        self.app = QApplication(sys.argv)
        self.app.setWindowIcon(QIcon(os.path.join("assets", "v-logo.png")))

        # Initialize the configuration manager to load settings
        ConfigManager.initialize()

        # Initialize the settings window
        self.settings_window = SettingsWindow()
        self.settings_window.settings_closed.connect(self.on_settings_closed)
        self.settings_window.settings_saved.connect(self.restart_app)

        # Check if a configuration file exists. If so, initialize components.
        # Otherwise, prompt the user to configure settings.
        if ConfigManager.config_file_exists():
            self.initialize_components()
        else:
            print("No valid configuration file found. Opening settings window...")
            self.settings_window.show()

    def initialize_components(self):
        """
        Initialize the core components of the application.
        This includes the input simulator, key listener, transcription model,
        result processing thread, and the main GUI window.
        """
        # Initialize input simulator for typing text
        self.input_simulator = InputSimulator()
        self.input_simulator.typingStarted.connect(self.on_typing_started)
        self.input_simulator.typingFinished.connect(self.on_typing_finished)

        # Initialize key listener for global hotkeys
        self.key_listener = KeyListener()
        self.key_listener.add_callback("on_activate", self.on_activation)
        self.key_listener.add_callback("on_deactivate", self.on_deactivation)
        self.key_listener.start()

        # Create the local Whisper model for transcription
        self.local_model = create_local_model()

        self.result_thread = None

        # Initialize the main window and connect its signals
        self.main_window = MainWindow()
        self.main_window.openSettings.connect(self.settings_window.show)
        self.main_window.startListening.connect(self.on_activation)
        self.main_window.stopListening.connect(self.on_activation)
        self.main_window.stopListeningAndDiscard.connect(self.stop_result_thread)
        self.main_window.closeApp.connect(self.exit_app)

        # Connect state change signals to update UI
        self.stateChanged.connect(self.main_window.set_state)
        self.stateChanged.connect(self.update_tray_menu)

        # Create system tray icon
        self.create_tray_icon()
        self.main_window.show()

    def create_tray_icon(self):
        """
        Create the system tray icon and its context menu.
        Allows the user to interact with the app from the system tray.
        """
        self.tray_icon = QSystemTrayIcon(
            QIcon(os.path.join("assets", "v-logo.png")), self.app
        )
        self.tray_icon.show()
        self.update_tray_menu("idle")

    def update_tray_menu(self, state):
        """
        Update the system tray icon's context menu based on the application's state.
        
        Args:
            state (str): The current state of the application ('idle', 'recording', etc.)
        """
        tray_menu = QMenu()

        # Action to show the main window
        show_action = QAction(QIcon(os.path.join("assets", "v-logo.png")), "viapp", self.app)
        show_action.triggered.connect(self.main_window.show)
        tray_menu.addAction(show_action)

        # Dynamic action based on state (Start/Stop recording)
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

        # Settings action
        settings_action = QAction(QIcon(os.path.join("assets", "gear.png")), "Settings", self.app)
        settings_action.triggered.connect(self.settings_window.show)
        tray_menu.addAction(settings_action)

        # Exit action
        exit_action = QAction(QIcon(os.path.join("assets", "exit.png")), "Exit", self.app)
        exit_action.triggered.connect(self.exit_app)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)

    def cleanup(self):
        """
        Clean up resources before exiting or restarting.
        Stops the key listener and input simulator.
        """
        if self.key_listener:
            self.key_listener.stop()
        if self.input_simulator:
            self.input_simulator.cleanup()

    def exit_app(self):
        """
        Exit the application gracefully.
        """
        self.cleanup()
        QApplication.quit()

    def restart_app(self):
        """
        Restart the application to apply new settings.
        """
        self.cleanup()
        QApplication.quit()
        QProcess.startDetached(sys.executable, sys.argv)

    def on_settings_closed(self):
        """
        Handle the event when the settings window is closed.
        If closed without saving on the first run, initialize with default values.
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
        Called when the activation key combination is pressed or the start button is clicked.
        Toggles the recording state.
        """
        self.main_window.show()
        # If already recording, stop recording
        if self.result_thread and self.result_thread.isRunning():
            recording_mode = ConfigManager.get_config_value(
                "recording_options", "recording_mode"
            )
            # For 'press_to_toggle' and 'continuous' modes, stopping is explicit
            if recording_mode in ("press_to_toggle", "continuous"):
                self.result_thread.stop_recording()
                self.stateChanged.emit("transcribing")
            return

        # Start recording
        self.start_result_thread()
        self.stateChanged.emit("recording")

    def on_deactivation(self):
        """
        Called when the activation key combination is released.
        Relevant only for 'hold_to_record' mode.
        """
        if (
            ConfigManager.get_config_value("recording_options", "recording_mode")
            in ("hold_to_record",)
        ):
            if self.result_thread and self.result_thread.isRunning():
                self.result_thread.stop_recording()
                self.stateChanged.emit("transcribing")

    def start_result_thread(self):
        """
        Start the result thread to record audio and transcribe it.
        Initializes the ResultThread and connects its signals.
        """
        if self.result_thread and self.result_thread.isRunning():
            return

        self.result_thread = ResultThread(self.local_model)
        self.result_thread.statusSignal.connect(self.on_status_update)
        self.result_thread.resultSignal.connect(self.on_transcription_complete)
        self.result_thread.partialResultSignal.connect(self.on_partial_transcription)
        self.result_thread.start()

    def stop_result_thread(self):
        """
        Stop the result thread immediately, discarding any ongoing recording.
        """
        if self.result_thread and self.result_thread.isRunning():
            self.result_thread.stop()
            self.stateChanged.emit("idle")

    def on_status_update(self, status):
        """
        Update the main window's state based on the result thread's status.
        
        Args:
            status (str): The new status ('recording', 'transcribing', 'idle', 'error')
        """
        self.stateChanged.emit(status)

    def on_partial_transcription(self, result):
        """
        Handle partial transcription results.
        Updates the main window with the current transcription progress.
        
        Args:
            result (str): The partial transcription text.
        """
        self.main_window.update_transcription_label(result)

    def on_transcription_complete(self, result):
        """
        Handle the completion of a transcription.
        Types the result into the active window and resets the state.
        
        Args:
            result (str): The final transcribed text.
        """
        self.input_simulator.typewrite(result)

        # If in continuous mode, restart the recording thread
        if (
            ConfigManager.get_config_value("recording_options", "recording_mode")
            == "continuous"
        ):
            self.start_result_thread()
        else:
            # We don't force "idle" here anymore because the input simulator 
            # will manage the "typing" -> "idle" transition via signals.
            # However, if we were "transcribing", we might want to ensure we don't get stuck.
            # But since typewrite is non-blocking, we are effectively done with this transcription task.
            # The typing signal will trigger immediately after this.
            pass

    def on_typing_started(self):
        """
        Handle the start of text typing.
        Updates state to 'typing' unless the user is currently recording.
        """
        # Prevent overriding the recording state if the user starts speaking while typing occurs
        if self.main_window.state != "recording":
            self.stateChanged.emit("typing")

    def on_typing_finished(self):
        """
        Handle the completion of text typing.
        Updates state to 'idle' only if the current state is 'typing'.
        """
        # Only revert to idle if we are currently in the typing state.
        # If the user started recording, we shouldn't switch to idle.
        if self.main_window.state == "typing":
            self.stateChanged.emit("idle")

    def run(self):
        """
        Start the application event loop.
        """
        sys.exit(self.app.exec_())


if __name__ == "__main__":
    app = viappApp()
    app.run()
