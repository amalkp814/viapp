 
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
from PyQt5.QtWidgets import QApplication, QPushButton, QHBoxLayout, QLabel
from PyQt5.QtCore import pyqtSignal, Qt

# Add parent directory to sys.path so we can import base_window
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ui.base_window import BaseWindow

class MainWindow(BaseWindow):
    # Signals allow this window to communicate with other parts of the app
    openSettings = pyqtSignal()    # Emitted when the Settings button is clicked
    startRecording = pyqtSignal()  # Emitted when the Start button is pressed to begin recording
    stopRecording = pyqtSignal()   # Emitted when the Stop action is requested
    closeApp = pyqtSignal()        # Emitted when the window is closed
    stopRequested = pyqtSignal()   # Emitted when the user presses Stop in the status area

    def __init__(self):
        """
        Initialize the main window.
        Sets up the window title, size, and main UI elements.
        """
        # Smaller, compact window for bottom-center placement
        super().__init__('WhisperWriter', 360, 120)
        self.initMainUI()

        # Status area (merged from previous StatusWindow)
        self.initStatusArea()

        # Place window bottom-center and allow dragging
        self.moveToBottomCenter()

        # Recording state
        self.is_recording = False

    def initMainUI(self):
        """
        Set up the main user interface with Start and Settings buttons.
        Buttons are centered horizontally.
        """
        # Start button: small round microphone toggle
        start_btn = QPushButton()
        start_btn.setCursor(Qt.PointingHandCursor)
        start_btn.setToolTip('Start / Stop recording')
        start_btn.setFixedSize(56, 56)
        start_btn.setCheckable(True)
        start_btn.clicked.connect(self.startPressed)
        # round styling and subtle shadow-like border for premium look
        start_btn.setStyleSheet('''
            QPushButton { border-radius: 28px; background-color: #2b2b2b; color: white; }
            QPushButton:checked { background-color: #c62828; }
        ''')
        # use a small mic icon if available
        mic_icon = None
        stop_icon = None
        try:
            mic_path = os.path.join('assets', 'microphone.png')
            stop_path = os.path.join('assets', 'pencil.png')
            mic_icon = QIcon(mic_path)
            stop_icon = QIcon(stop_path)
            start_btn.setIcon(mic_icon)
            start_btn.setIconSize(start_btn.size() * 0.6)
        except Exception:
            pass
        self.start_btn = start_btn
        self._mic_icon = mic_icon
        self._stop_icon = stop_icon

        # Settings button: icon-only with a gear-like style
        settings_btn = QPushButton()
        settings_btn.setCursor(Qt.PointingHandCursor)
        settings_btn.setFixedSize(36, 36)
        settings_btn.setToolTip('Open settings')
        settings_btn.setStyleSheet('''
            QPushButton { border-radius: 6px; background-color: transparent; }
            QPushButton:hover { background-color: rgba(255,255,255,0.04); }
        ''')
        try:
            settings_icon = self.style().standardIcon(self.style().SP_FileDialogDetailedView)
            settings_btn.setIcon(settings_icon)
            settings_btn.setIconSize(settings_btn.size() * 0.6)
        except Exception:
            settings_btn.setText('⚙')
        settings_btn.clicked.connect(self.openSettings.emit)

        # Layout: center the buttons horizontally, settings on the left
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(settings_btn)
        button_layout.addSpacing(10)
        button_layout.addWidget(start_btn)
        button_layout.addStretch(1)

        # Add vertical spacers to center buttons vertically
        self.main_layout.addStretch(1)
        self.main_layout.addLayout(button_layout)
        # Add a small caption under the mic button
        caption = QLabel('Start / Stop')
        caption.setAlignment(Qt.AlignCenter)
        caption.setFont(QFont('Segoe UI', 8))
        caption.setStyleSheet('color: #666666;')
        self.main_layout.addWidget(caption)
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
        # Toggle recording state: start or stop recording
        if not getattr(self, 'is_recording', False):
            self.is_recording = True
            # visual toggle
            try:
                self.start_btn.setChecked(True)
                if self._stop_icon:
                    self.start_btn.setIcon(self._stop_icon)
                else:
                    self.start_btn.setText('Stop')
            except Exception:
                pass
            self.startRecording.emit()
        else:
            self.is_recording = False
            try:
                self.start_btn.setChecked(False)
                if self._mic_icon:
                    self.start_btn.setIcon(self._mic_icon)
                else:
                    self.start_btn.setText('Start')
            except Exception:
                pass
            self.stopRecording.emit()

    # ---- Status area API (merged from StatusWindow) ----
    def initStatusArea(self):
        """
        Initialize a small status area inside the main window to show recording/transcribing state.
        Contains an icon, a label, and a stop button (to cancel recording/process).
        """
        # Container layout for the status row
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(0, 10, 0, 0)

        # Icon
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(24, 24)
        mic_icon_path = os.path.join('assets', 'microphone.png')
        pencil_icon_path = os.path.join('assets', 'pencil.png')
        try:
            from PyQt5.QtGui import QPixmap
            self.microphone_pixmap = QPixmap(mic_icon_path).scaled(24, 24)
            self.pencil_pixmap = QPixmap(pencil_icon_path).scaled(24, 24)
            self.icon_label.setPixmap(self.microphone_pixmap)
        except Exception:
            self.microphone_pixmap = None
            self.pencil_pixmap = None

        # Status text
        self.status_label = QLabel('Idle')
        self.status_label.setFont(QFont('Segoe UI', 10))
        self.status_label.setStyleSheet('color: #666666;')

        # No separate stop button - Start/shortcut toggles recording

        status_layout.addWidget(self.icon_label)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch(1)
        # status_layout.addWidget(self.stop_button)  # removed separate stop button

        self.main_layout.addLayout(status_layout)

    def updateStatus(self, status: str):
        """
        Update the inline status area based on status string.
        Expected statuses: 'recording', 'transcribing', 'idle', 'error', 'cancel'
        """
        if status == 'recording':
            if self.microphone_pixmap:
                self.icon_label.setPixmap(self.microphone_pixmap)
            self.status_label.setText('Recording...')
            # no separate stop button; keep status_label updated
        elif status == 'transcribing':
            if self.pencil_pixmap:
                self.icon_label.setPixmap(self.pencil_pixmap)
            self.status_label.setText('Transcribing...')
            # no separate stop button; keep status_label updated
        elif status in ('idle', 'error', 'cancel'):
            self.status_label.setText('Idle')
            # no separate stop button; keep status_label updated

    def on_stop_requested(self):
        """
        This method is called when the user presses the Stop button in the main window.
        It emits the closeApp signal by default to allow the app to handle stopping.
        The app (main.py) should connect this to stop_result_thread or other cancellation logic.
        """
        # Emit a dedicated stopRequested signal for stopping recording/transcription
        self.stopRequested.emit()
        # Also update button state if Start button is present
        if getattr(self, 'is_recording', False):
            self.is_recording = False
            try:
                self.start_btn.setText('Start')
            except Exception:
                pass
        # Also emit stopRecording for consistency
        self.stopRecording.emit()

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
