
# Standard library imports
import os  # For file and path operations
import sys  # For system-specific parameters and functions
import time  # For timing operations (not used here)

# Third-party library imports
from audioplayer import AudioPlayer  # For playing audio files
from pynput.keyboard import Controller  # For simulating keyboard input

# PyQt5 imports for GUI and threading
from PyQt5.QtCore import QObject, QProcess  # QObject is base for all Qt objects, QProcess for restarting app
from PyQt5.QtGui import QIcon  # For window and tray icons
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction, QMessageBox  # GUI components

# Local module imports
from key_listener import KeyListener  # Listens for keyboard shortcuts
from result_thread import ResultThread  # Handles audio recording and transcription in a thread
from ui.main_window import MainWindow  # Main application window
from ui.settings_window import SettingsWindow  # Settings window
from ui.status_window import StatusWindow  # Status window (shows current state)
from transcription import create_local_model  # Function to create local transcription model
from input_simulation import InputSimulator  # Simulates typing the transcribed text
from utils import ConfigManager  # Manages configuration and settings



# Main application class for WhisperWriter
class WhisperWriterApp(QObject):
    def __init__(self):
        """
        Initialize the application, opening settings window if no configuration file is found.
        This sets up the main app, loads configuration, and shows the settings window if needed.
        """
        super().__init__()
        # Create the Qt application object
        self.app = QApplication(sys.argv)
        # Set the window icon (shown in taskbar and tray)
        self.app.setWindowIcon(QIcon(os.path.join('assets', 'ww-logo.png')))

        # Initialize configuration manager (loads config files)
        ConfigManager.initialize()

        # Create the settings window
        self.settings_window = SettingsWindow()
        # Connect signals for when settings are closed or saved
        self.settings_window.settings_closed.connect(self.on_settings_closed)
        self.settings_window.settings_saved.connect(self.restart_app)

        # If config file exists, initialize main components; otherwise, show settings window
        if ConfigManager.config_file_exists():
            self.initialize_components()
        else:
            print('No valid configuration file found. Opening settings window...')
            self.settings_window.show()


    def initialize_components(self):
        """
        Initialize the components of the application.
        This sets up the main window, key listener, input simulator, model, and tray icon.
        """
        # Create input simulator (for typing transcribed text)
        self.input_simulator = InputSimulator()

        # Create key listener (listens for activation/deactivation hotkeys)
        self.key_listener = KeyListener()
        self.key_listener.add_callback("on_activate", self.on_activation)
        self.key_listener.add_callback("on_deactivate", self.on_deactivation)

        # Load model options from config
        model_options = ConfigManager.get_config_section('model_options')
        model_path = model_options.get('local', {}).get('model_path')
        # Create local model if not using API
        self.local_model = create_local_model() if not model_options.get('use_api') else None

        self.result_thread = None  # Will be created when needed

        # Create main window (UI)
        self.main_window = MainWindow()
        self.main_window.openSettings.connect(self.settings_window.show)  # Open settings window
        self.main_window.startListening.connect(self.key_listener.start)  # Start listening for hotkeys
        self.main_window.closeApp.connect(self.exit_app)  # Exit app when requested

        # Create status window if not hidden in config
        if not ConfigManager.get_config_value('misc', 'hide_status_window'):
            self.status_window = StatusWindow()

        # Create system tray icon and menu
        self.create_tray_icon()
        # Show the main window
        self.main_window.show()


    def create_tray_icon(self):
        """
        Create the system tray icon and its context menu.
        This allows the user to access the app from the system tray.
        """
        # Create tray icon with app logo
        self.tray_icon = QSystemTrayIcon(QIcon(os.path.join('assets', 'ww-logo.png')), self.app)

        tray_menu = QMenu()  # Context menu for tray icon

        # Add menu item to show main window
        show_action = QAction('WhisperWriter Main Menu', self.app)
        show_action.triggered.connect(self.main_window.show)
        tray_menu.addAction(show_action)

        # Add menu item to open settings
        settings_action = QAction('Open Settings', self.app)
        settings_action.triggered.connect(self.settings_window.show)
        tray_menu.addAction(settings_action)

        # Add menu item to exit app
        exit_action = QAction('Exit', self.app)
        exit_action.triggered.connect(self.exit_app)
        tray_menu.addAction(exit_action)

        # Set the context menu and show the tray icon
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()


    def cleanup(self):
        """
        Clean up resources before exiting or restarting the app.
        Stops the key listener and cleans up the input simulator.
        """
        if self.key_listener:
            self.key_listener.stop()
        if self.input_simulator:
            self.input_simulator.cleanup()


    def exit_app(self):
        """
        Exit the application.
        Calls cleanup and quits the Qt application.
        """
        self.cleanup()
        QApplication.quit()


    def restart_app(self):
        """
        Restart the application to apply the new settings.
        Cleans up, quits, and starts a new process.
        """
        self.cleanup()
        QApplication.quit()
        QProcess.startDetached(sys.executable, sys.argv)


    def on_settings_closed(self):
        """
        If settings is closed without saving on first run, initialize the components with default values.
        Shows a message box and initializes components.
        """
        if not os.path.exists(os.path.join('src', 'config.yaml')):
            QMessageBox.information(
                self.settings_window,
                'Using Default Values',
                'Settings closed without saving. Default values are being used.'
            )
            self.initialize_components()


    def on_activation(self):
        """
        Called when the activation key combination is pressed.
        Handles starting or stopping recording depending on the mode.
        """
        if self.result_thread and self.result_thread.isRunning():
            recording_mode = ConfigManager.get_config_value('recording_options', 'recording_mode')
            if recording_mode == 'press_to_toggle':
                self.result_thread.stop_recording()
            elif recording_mode == 'continuous':
                self.stop_result_thread()
            return

        self.start_result_thread()


    def on_deactivation(self):
        """
        Called when the activation key combination is released.
        Stops recording if in 'hold_to_record' mode.
        """
        if ConfigManager.get_config_value('recording_options', 'recording_mode') == 'hold_to_record':
            if self.result_thread and self.result_thread.isRunning():
                self.result_thread.stop_recording()


    def start_result_thread(self):
        """
        Start the result thread to record audio and transcribe it.
        Creates and starts the thread, connects signals for status and results.
        """
        if self.result_thread and self.result_thread.isRunning():
            return

        self.result_thread = ResultThread(self.local_model)
        if not ConfigManager.get_config_value('misc', 'hide_status_window'):
            self.result_thread.statusSignal.connect(self.status_window.updateStatus)
            self.status_window.closeSignal.connect(self.stop_result_thread)
        self.result_thread.resultSignal.connect(self.on_transcription_complete)
        self.result_thread.start()


    def stop_result_thread(self):
        """
        Stop the result thread.
        Calls stop on the thread if it is running.
        """
        if self.result_thread and self.result_thread.isRunning():
            self.result_thread.stop()


    def on_transcription_complete(self, result):
        """
        When the transcription is complete, type the result and start listening for the activation key again.
        This is called when the result thread emits a result.
        """
        # Type the transcribed text using input simulator
        self.input_simulator.typewrite(result)

        # Play a beep sound if enabled in config
        if ConfigManager.get_config_value('misc', 'noise_on_completion'):
            AudioPlayer(os.path.join('assets', 'beep.wav')).play(block=True)

        # If in continuous mode, start a new result thread; otherwise, start listening for activation key
        if ConfigManager.get_config_value('recording_options', 'recording_mode') == 'continuous':
            self.start_result_thread()
        else:
            self.key_listener.start()


    def run(self):
        """
        Start the application.
        This enters the Qt event loop and keeps the app running.
        """
        sys.exit(self.app.exec_())


# Entry point for the application
if __name__ == '__main__':
    app = WhisperWriterApp()  # Create the app instance
    app.run()  # Run the app
