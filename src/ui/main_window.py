
# =============================
# main_window.py (with comments)
# =============================
# This file defines the MainWindow class for viapp's main UI.
# Beginners: This is the first window you see when you start viapp.
# It lets you start the keyboard listener or open the settings window.
#
# Key PyQt5 concepts:
# - Signals: Used to communicate between UI components (openSettings, startListening, closeApp)
# - QPushButton: Button widget
# - QHBoxLayout: Horizontal layout for arranging buttons
# - Inherits from BaseWindow for custom look and behavior

import os
import sys
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication, QPushButton, QHBoxLayout
from PyQt5.QtCore import pyqtSignal

# Add parent directory to sys.path so we can import base_window
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ui.base_window import BaseWindow

class MainWindow(BaseWindow):
    # Signals allow this window to communicate with other parts of the app
    openSettings = pyqtSignal()    # Emitted when the Settings button is clicked
    startListening = pyqtSignal()  # Emitted when the Start button is clicked
    closeApp = pyqtSignal()        # Emitted when the window is closed

    def __init__(self):
        """
        Initialize the main window.
        Sets up the window title, size, and main UI elements.
        """
        super().__init__('WhisperWriter', 320, 180)  # TODO: Update to 'viapp' if needed
        self.initMainUI()

    def initMainUI(self):
        """
        Set up the main user interface with Start and Settings buttons.
        Buttons are centered horizontally.
        """
        # Start button: begins keyboard listening/transcription
        start_btn = QPushButton('Start')
        start_btn.setFont(QFont('Segoe UI', 10))
        start_btn.setFixedSize(120, 60)
        start_btn.clicked.connect(self.startPressed)

        # Settings button: opens the settings window
        settings_btn = QPushButton('Settings')
        settings_btn.setFont(QFont('Segoe UI', 10))
        settings_btn.setFixedSize(120, 60)
        settings_btn.clicked.connect(self.openSettings.emit)

        # Layout: center the buttons horizontally
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)           # Spacer (left)
        button_layout.addWidget(start_btn)    # Start button
        button_layout.addWidget(settings_btn) # Settings button
        button_layout.addStretch(1)           # Spacer (right)

        # Add vertical spacers to center buttons vertically
        self.main_layout.addStretch(1)
        self.main_layout.addLayout(button_layout)
        self.main_layout.addStretch(1)

    def closeEvent(self, event):
        """
        Called when the main window is closed.
        Emits the closeApp signal to notify the app to exit.
        """
        self.closeApp.emit()

    def startPressed(self):
        """
        Called when the Start button is pressed.
        Emits the startListening signal and hides the main window.
        """
        self.startListening.emit()
        self.hide()

# If this file is run directly, show the main window
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
