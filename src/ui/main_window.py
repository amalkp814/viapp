
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
from PyQt5.QtGui import QFont, QPixmap, QGuiApplication, QIcon
from PyQt5.QtWidgets import QApplication, QPushButton, QHBoxLayout, QLabel, QWidget
from PyQt5.QtCore import pyqtSignal, Qt

# Add parent directory to sys.path so we can import base_window
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ui.base_window import BaseWindow

class MainWindow(BaseWindow):
    # Signals allow this window to communicate with other parts of the app
    openSettings = pyqtSignal()    # Emitted when the Settings button is clicked
    startRecording = pyqtSignal()  # Emitted when the Start button is pressed to begin recording
    stopRecording = pyqtSignal()   # Emitted when the Stop action is requested
    processFile = pyqtSignal()     # Emitted when the Process File button is clicked
    closeApp = pyqtSignal()        # Emitted when the window is closed
    stopRequested = pyqtSignal()   # Emitted when the user presses Stop in the status area

    def __init__(self):
        """
        Initialize the main window.
        Sets up the window title, size, and main UI elements.
        """
        # Smaller, compact window for bottom-center placement
        super().__init__('viapp', 240, 100)

        # Initialize UI components
        self.initStatusArea() # Must be called before initMainUI
        self.initMainUI()

        # Place window bottom-center and allow dragging
        self.moveToBottomCenter()

        # Recording state
        self.is_recording = False

    def initMainUI(self):
        """
        Set up the main user interface with Start and Settings buttons.
        """
        # Start button: small round microphone toggle
        start_btn = QPushButton()
        start_btn.setCursor(Qt.PointingHandCursor)
        start_btn.setToolTip('Start / Stop recording')
        start_btn.setFixedSize(56, 56)
        start_btn.setCheckable(True)
        start_btn.clicked.connect(self.startPressed)
        self.start_btn = start_btn

        # Settings button: icon-only with a gear-like style
        settings_btn = QPushButton()
        settings_btn.setCursor(Qt.PointingHandCursor)
        settings_btn.setFixedSize(36, 36)
        settings_btn.setToolTip('Open settings')
        settings_btn.setStyleSheet('''
            QPushButton { border-radius: 18px; background-color: transparent; }
            QPushButton:hover { background-color: rgba(0,0,0,0.04); }
        ''')
        try:
            settings_icon = self.style().standardIcon(self.style().SP_FileDialogOptions)
            settings_btn.setIcon(settings_icon)
            settings_btn.setIconSize(settings_btn.size() * 0.6)
        except Exception:
            settings_btn.setText('⚙')
        settings_btn.clicked.connect(self.openSettings.emit)

        # Process File button
        process_file_btn = QPushButton()
        process_file_btn.setCursor(Qt.PointingHandCursor)
        process_file_btn.setFixedSize(36, 36)
        process_file_btn.setToolTip('Process audio file')
        process_file_btn.setStyleSheet('''
            QPushButton { border-radius: 18px; background-color: transparent; }
            QPushButton:hover { background-color: rgba(0,0,0,0.04); }
        ''')
        try:
            process_file_icon = self.style().standardIcon(self.style().SP_FileIcon)
            process_file_btn.setIcon(process_file_icon)
            process_file_btn.setIconSize(process_file_btn.size() * 0.6)
        except Exception:
            process_file_btn.setText('F')
        process_file_btn.clicked.connect(self.processFile.emit)

        # Layout: mike on the left, settings on the right
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(10, 0, 10, 0) # Add horizontal margins
        button_layout.addWidget(self.start_btn)
        button_layout.addStretch(1)
        button_layout.addWidget(process_file_btn)
        button_layout.addWidget(settings_btn)

        self.main_layout.addLayout(button_layout)

        # Initialize icons
        self.mic_icon = None
        self.pencil_icon = None
        try:
            mic_path = os.path.join('assets', 'microphone.png')
            pencil_path = os.path.join('assets', 'pencil.png')
            self.mic_icon = QIcon(mic_path)
            self.pencil_icon = QIcon(pencil_path)
            self.start_btn.setIconSize(self.start_btn.size() * 0.6)
        except Exception:
            pass

        self.updateStatus('idle')

    def closeEvent(self, event):
        """
        Called when the main window is closed.
        Emits the closeApp signal to notify the app to exit.
        """
        self.closeApp.emit()

    def startPressed(self):
        """
        Called when the Start button is pressed.
        Toggles the recording state.
        """
        self.is_recording = not self.is_recording
        if self.is_recording:
            self.startRecording.emit()
        else:
            self.stopRecording.emit()
        self.updateStatus('recording' if self.is_recording else 'idle')

    # ---- Status area API (merged from StatusWindow) ----
    def initStatusArea(self):
        """
        Initialize a small status area inside the main window to show recording/transcribing state.
        """
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)

        self.status_label = QLabel('Idle')
        self.status_label.setFont(QFont('Segoe UI', 10))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet('color: #666666;')
        status_layout.addWidget(self.status_label)
        self.main_layout.addWidget(status_widget)

    def updateStatus(self, status: str):
        """
        Update the inline status area based on status string.
        Expected statuses: 'recording', 'transcribing', 'idle', 'error', 'cancel'
        """
        if status == 'recording':
            self.status_label.setText('Recording...')
            if self.mic_icon:
                self.start_btn.setIcon(self.mic_icon)
            self.start_btn.setStyleSheet('''
                QPushButton { border-radius: 28px; background-color: #81c784; color: #1b5e20; }
            ''') # light green and dark blue
        elif status == 'transcribing':
            self.status_label.setText('Transcribing...')
            if self.pencil_icon:
                self.start_btn.setIcon(self.pencil_icon)
            self.start_btn.setStyleSheet('''
                QPushButton { border-radius: 28px; background-color: #ffb74d; color: #e65100; }
            ''') # light orange and dark orange
        elif status in ('idle', 'error', 'cancel'):
            self.is_recording = False
            self.status_label.setText('Idle')
            if self.mic_icon:
                self.start_btn.setIcon(self.mic_icon)
            self.start_btn.setStyleSheet('''
                QPushButton { border-radius: 28px; background-color: #90caf9; color: #424242; }
            ''') # light blue and dark grey

    def on_stop_requested(self):
        """
        This method is called when the user presses the Stop button in the main window.
        """
        self.stopRequested.emit()
        self.updateStatus('idle')

    def moveToBottomCenter(self):
        """Move the window to the bottom center of the primary screen."""
        screen = QGuiApplication.primaryScreen()
        if not screen:
            return
        rect = screen.availableGeometry()
        window_width = self.width()
        window_height = self.height()
        x = rect.x() + (rect.width() - window_width) // 2
        y = rect.y() + rect.height() - window_height - 80  # 80px above bottom
        self.move(x, y)

# If this file is run directly, show the main window
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
