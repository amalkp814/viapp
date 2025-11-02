import os
import sys
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import QApplication, QPushButton, QHBoxLayout, QVBoxLayout, QLabel
from PyQt5.QtCore import pyqtSignal, Qt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ui.base_window import BaseWindow


class MainWindow(BaseWindow):
    openSettings = pyqtSignal()
    startListening = pyqtSignal()
    stopListening = pyqtSignal()
    stopListeningAndDiscard = pyqtSignal()
    closeApp = pyqtSignal()

    def __init__(self):
        """
        Initialize the main window.
        """
        super().__init__("viapp", 320, 240)
        self.initMainUI()
        self.set_state("idle")

    def initMainUI(self):
        """
        Initialize the main user interface.
        """
        # Main vertical layout
        main_v_layout = QVBoxLayout()

        main_v_layout.addStretch(1)

        # Middle layout for settings and main button
        middle_layout = QHBoxLayout()
        middle_layout.addStretch(1)

        # Central button
        self.central_button = QPushButton()
        self.central_button.setFixedSize(120, 120)
        self.central_button.setIconSize(self.central_button.size() * 0.5)
        self.central_button.clicked.connect(self.on_central_button_clicked)
        middle_layout.addWidget(self.central_button)

        # Settings button
        settings_btn = QPushButton()
        settings_btn.setFixedSize(30, 30)
        settings_btn.setIcon(QIcon(os.path.join("assets", "gear.png")))
        settings_btn.setIconSize(settings_btn.size() * 0.8)
        settings_btn.setStyleSheet("background-color: transparent; border: none;")
        settings_btn.clicked.connect(self.openSettings.emit)

        # Use a QVBoxLayout to align the settings button to the middle
        settings_layout = QVBoxLayout()
        settings_layout.addStretch(1)
        settings_layout.addWidget(settings_btn)
        settings_layout.addStretch(1)
        middle_layout.addLayout(settings_layout)

        middle_layout.addStretch(1)
        main_v_layout.addLayout(middle_layout)

        main_v_layout.addStretch(1)

        # Bottom layout for status label
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch(1)
        self.status_label = QLabel("Click the button to start recording.")
        self.status_label.setFont(QFont("Segoe UI", 10))
        bottom_layout.addWidget(self.status_label)
        bottom_layout.addStretch(1)
        main_v_layout.addLayout(bottom_layout)

        self.main_layout.addLayout(main_v_layout)

    def set_state(self, state):
        self.state = state
        if state == "idle":
            self.central_button.setIcon(QIcon(os.path.join("assets", "microphone.png")))
            self.central_button.setStyleSheet(
                "background-color: #cccccc; border-radius: 60px;"
            )
            self.status_label.setText("Click the button to start recording.")
        elif state == "recording":
            self.central_button.setIcon(QIcon(os.path.join("assets", "microphone.png")))
            self.central_button.setStyleSheet(
                "background-color: #3498db; border-radius: 60px;"
            )
            self.status_label.setText("Recording...")
        elif state == "transcribing":
            self.central_button.setIcon(QIcon(os.path.join("assets", "pencil.png")))
            self.central_button.setStyleSheet(
                "background-color: #f1c40f; border-radius: 60px;"
            )
            self.status_label.setText("Transcribing...")

    def update_transcription_label(self, text):
        words = text.split()
        self.status_label.setText(" ".join(words[-5:]))

    def on_central_button_clicked(self):
        if self.state == "idle":
            self.startListening.emit()
            self.set_state("recording")
        elif self.state == "recording":
            self.stopListening.emit()
            self.set_state("transcribing")

    def closeEvent(self, event):
        """
        Override the close event to hide the window instead of closing it.
        """
        if self.state == "recording":
            self.stopListeningAndDiscard.emit()
        event.ignore()
        self.hide()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
