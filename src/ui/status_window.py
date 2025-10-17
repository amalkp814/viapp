 
# =============================
# status_window.py (with comments)
# =============================
# This file defines the StatusWindow class for viapp's status UI.
# Beginners: This window shows the current status (recording, transcribing, etc.)
# with an icon and message. It appears at the bottom of the screen and updates automatically.
#
# Key PyQt5 concepts:
# - Signals: Used to update status from other threads/components
# - QPixmap: For displaying icons
# - QHBoxLayout: Horizontal layout for icon and label
# - Window positioning: Custom placement at bottom center
#
# Key viapp concepts:
# - Status updates: Shows 'Recording...', 'Transcribing...', or hides on idle/error/cancel

import sys
import os
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer
from PyQt5.QtGui import QFont, QPixmap, QIcon
from PyQt5.QtWidgets import QApplication, QLabel, QHBoxLayout

# Add parent directory to sys.path so we can import base_window
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ui.base_window import BaseWindow

class StatusWindow(BaseWindow):
    # Signals for updating status and handling close events
    statusSignal = pyqtSignal(str)  # Used to update the status ('recording', 'transcribing', etc.)
    closeSignal = pyqtSignal()      # Emitted when the window is closed

    def __init__(self):
        """
        Initialize the status window.
        Sets up the UI and connects the status update signal.
        """
        super().__init__('viapp Status', 320, 120)
        self.initStatusUI()
        self.statusSignal.connect(self.updateStatus)

    def initStatusUI(self):
        """
        Set up the status window UI:
        - Frameless, always-on-top window
        - Shows an icon (microphone or pencil) and status text
        """
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(0, 0, 0, 0)

        # Icon label: shows microphone or pencil depending on status
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(32, 32)
        microphone_path = os.path.join('assets', 'microphone.png')
        pencil_path = os.path.join('assets', 'pencil.png')
        self.microphone_pixmap = QPixmap(microphone_path).scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.pencil_pixmap = QPixmap(pencil_path).scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.icon_label.setPixmap(self.microphone_pixmap)
        self.icon_label.setAlignment(Qt.AlignCenter)

        # Status label: shows text like 'Recording...' or 'Transcribing...'
        self.status_label = QLabel('Recording...')
        self.status_label.setFont(QFont('Segoe UI', 12))

        # Center icon and label horizontally
        status_layout.addStretch(1)
        status_layout.addWidget(self.icon_label)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch(1)

        self.main_layout.addLayout(status_layout)
    def show(self):
        """
        Position the window at the bottom center of the screen and show it.
        This keeps the status window visible but unobtrusive.
        """
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()
        window_width = self.width()
        window_height = self.height()

        x = (screen_width - window_width) // 2
        y = screen_height - window_height - 120  # 120px above bottom

        self.move(x, y)
        super().show()
    def closeEvent(self, event):
        """
        Called when the status window is closed.
        Emits the closeSignal for other components to react.
        """
        self.closeSignal.emit()
        super().closeEvent(event)

    @pyqtSlot(str)
    def updateStatus(self, status):
        """
        Update the status window based on the given status string.
        - 'recording': show microphone icon and 'Recording...'
        - 'transcribing': show pencil icon and 'Transcribing...'
        - 'idle', 'error', 'cancel': close the window
        """
        if status == 'recording':
            self.icon_label.setPixmap(self.microphone_pixmap)
            self.status_label.setText('Recording...')
            self.show()
        elif status == 'transcribing':
            self.icon_label.setPixmap(self.pencil_pixmap)
            self.status_label.setText('Transcribing...')

        if status in ('idle', 'error', 'cancel'):
            self.close()


if __name__ == '__main__':
    # Demo: Show the status window and simulate status changes
    app = QApplication(sys.argv)
    
    status_window = StatusWindow()
    status_window.show()

    # Simulate status updates (for testing/demo purposes)
    QTimer.singleShot(3000, lambda: status_window.statusSignal.emit('transcribing'))
    QTimer.singleShot(6000, lambda: status_window.statusSignal.emit('idle'))
    
    sys.exit(app.exec_())
