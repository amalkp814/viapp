
# =============================
# base_window.py (with comments)
# =============================
# This file defines the BaseWindow class, which provides a custom window for viapp using PyQt5.
# Beginners: This is the foundation for all main windows in the app. It creates a frameless, draggable window
# with a rounded rectangle background, a custom title bar, and a close button.
#
# Key PyQt5 concepts:
# - QMainWindow: Main window class in PyQt5
# - QWidget: Basic UI element
# - QVBoxLayout/QHBoxLayout: Layout managers for arranging widgets
# - QPainter: Used for custom drawing (rounded corners, transparency)
# - Events: mousePressEvent, mouseMoveEvent, etc. allow for custom window behavior

from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QBrush, QColor, QFont, QPainterPath, QGuiApplication
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QMainWindow


class BaseWindow(QMainWindow):
    """
    BaseWindow is a custom main window for viapp.
    It provides a frameless, rounded, draggable window with a title bar and close button.
    Other windows in viapp inherit from this class.
    """
    def __init__(self, title, width, height):
        """
        Initialize the base window.
        Args:
            title (str): Window title text
            width (int): Window width in pixels
            height (int): Window height in pixels
        """
        super().__init__()
        self.initUI(title, width, height)  # Set up the UI elements
        self.setWindowPosition()           # Center the window on the screen
        self.is_dragging = False           # Used for window dragging

    def initUI(self, title, width, height):
        """
        Set up the user interface for the window.
        - Frameless, translucent, fixed size
        - Custom title bar with app name and close button
        """
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.FramelessWindowHint)  # Remove default window borders
        self.setAttribute(Qt.WA_TranslucentBackground, True)  # Allow transparency
        self.setFixedSize(width, height)

        self.main_widget = QWidget(self)
        self.main_layout = QVBoxLayout(self.main_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        # Title bar section
        title_bar = QWidget()
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(0, 0, 0, 0)

        # Title label (shows app name)
        title_label = QLabel('WhisperWriter')  # TODO: Update to 'viapp' if needed
        title_label.setFont(QFont('Segoe UI', 12, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #404040;")

        # Close button (top right)
        close_button_widget = QWidget()
        close_button_layout = QHBoxLayout(close_button_widget)
        close_button_layout.setContentsMargins(0, 0, 0, 0)

        close_button = QPushButton('×')
        close_button.setFixedSize(25, 25)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: #404040;
            }
            QPushButton:hover {
                color: #000000;
            }
        """)
        close_button.clicked.connect(self.handleCloseButton)  # Connect button to close method

        close_button_layout.addWidget(close_button, alignment=Qt.AlignRight)

        # Add widgets to the title bar layout
        title_bar_layout.addWidget(QWidget(), 1)  # Left spacer for alignment
        title_bar_layout.addWidget(title_label, 3)  # Title label (centered)
        title_bar_layout.addWidget(close_button_widget, 1)  # Close button (right)

        self.main_layout.addWidget(title_bar)
        self.setCentralWidget(self.main_widget)

    def setWindowPosition(self):
        """
        Center the window on the user's screen.
        This makes the app appear in the middle when opened.
        """
        center_point = QGuiApplication.primaryScreen().availableGeometry().center()
        frame_geometry = self.frameGeometry()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())

    def handleCloseButton(self):
        """
        Called when the close button is clicked. Closes the window.
        """
        self.close()

    def mousePressEvent(self, event):
        """
        Start dragging the window when the user clicks and holds the left mouse button.
        """
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.start_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """
        Move the window as the user drags it with the mouse.
        """
        if Qt.LeftButton and self.is_dragging:
            self.move(event.globalPos() - self.start_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        """
        Stop dragging the window when the mouse button is released.
        """
        self.is_dragging = False

    def paintEvent(self, event):
        """
        Custom paint event to draw a rounded rectangle with a semi-transparent white background.
        This gives the window a modern, soft look.
        """
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 20, 20)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor(255, 255, 255, 220)))
        painter.setPen(Qt.NoPen)
        painter.drawPath(path)
