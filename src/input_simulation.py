import sys
import time
import subprocess
import re
from pynput.keyboard import Controller as PynputController

from utils import ConfigManager


import threading
from queue import Queue

from PyQt5.QtCore import QObject, pyqtSignal

class _BaseSimulator(QObject):
    """
    A base class for input simulators that handles word replacements.
    Provides common functionality for text preprocessing before typing.
    """
    typingStarted = pyqtSignal()
    typingFinished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.input_queue = Queue()
        self.worker_thread = threading.Thread(target=self._input_worker, daemon=True)
        self.worker_thread.start()

    def typewrite(self, text):
        """
        Add text to the input queue to be typed by the worker thread.
        This method is non-blocking.
        """
        self.input_queue.put(text)

    def _input_worker(self):
        """
        Worker thread that processes the input queue and types text sequentially.
        """
        while True:
            text = self.input_queue.get()
            self.typingStarted.emit()
            try:
                self._do_typewrite(text)
            except Exception as e:
                ConfigManager.console_print(f"Input error: {e}")
            finally:
                self.input_queue.task_done()
                if self.input_queue.empty():
                    self.typingFinished.emit()

    def _do_typewrite(self, text):
        """
        Abstract method for the actual typing logic.
        Must be implemented by subclasses.
        """
        raise NotImplementedError

    def _perform_word_replacements(self, text):
        """
        Replace words in the text based on the configuration.
        Uses regex word boundaries to ensure only whole words are replaced.
        
        Args:
            text (str): The input text to process.
            
        Returns:
            str: The text with replacements applied.
        """
        word_replacements = ConfigManager.get_config_value(
            "post_processing", "word_replacements"
        )
        if word_replacements:
            for old, new in word_replacements.items():
                # Use word boundaries to avoid replacing substrings within other words
                text = re.sub(
                    r"\b" + re.escape(old) + r"\b", new, text, flags=re.IGNORECASE
                )
        return text


class _PynputSimulator(_BaseSimulator):
    """
    A class to simulate keyboard input using pynput.
    This is the cross-platform default simulator.
    """

    def __init__(self):
        super().__init__()
        self.keyboard = PynputController()

    def _do_typewrite(self, text):
        """
        Simulate typing the given text character by character.
        
        Args:
            text (str): The text to type.
        """
        from pynput.keyboard import Key

        text = self._perform_word_replacements(text)
        interval = ConfigManager.get_config_value(
            "post_processing", "writing_key_press_delay"
        )
        for char in text:
            self.keyboard.press(char)
            self.keyboard.release(char)
            time.sleep(interval)
        
        # Force Flush Strategy:
        # Simulate a harmless key press to flush the OS buffer.
        # This is often required for applications that buffer input (like some editors or remote desktops).
        time.sleep(0.01)
        self.keyboard.touch(Key.shift, False) # Release shift just in case
        time.sleep(0.01)

    def cleanup(self):
        """
        Cleanup resources. No specific cleanup needed for pynput.
        """
        pass


class _YdotoolSimulator(_BaseSimulator):
    """
    A class to simulate keyboard input using ydotool.
    This is a Linux-specific simulator that works on Wayland.
    """
    def __init__(self):
        super().__init__()

    def _do_typewrite(self, text):
        """
        Simulate typing the given text using ydotool.
        
        Args:
            text (str): The text to type.
        """
        text = self._perform_word_replacements(text)
        try:
            # Add a small delay to allow the user to switch windows
            time.sleep(0.1)
            subprocess.run(["ydotool", "type", text], check=True)
        except FileNotFoundError:
            ConfigManager.console_print(
                "Error: 'ydotool' is not installed or not in your PATH. Please install it to use this input method."
            )
        except Exception as e:
            ConfigManager.console_print(f"An error occurred while using ydotool: {e}")

    def cleanup(self):
        """
        Cleanup resources. No specific cleanup needed for ydotool.
        """
        pass


class InputSimulator:
    """
    A factory class that returns the appropriate input simulator based on the configuration.
    """

    def __new__(cls):
        """
        Create and return an instance of the appropriate simulator class.
        Checks platform and availability of tools (like ydotool on Linux).
        """
        input_method = ConfigManager.get_config_value("post_processing", "input_method")

        if input_method == "auto":
            if sys.platform == "linux":
                if cls._is_ydotool_available():
                    ConfigManager.console_print("Using ydotool for input simulation.")
                    return _YdotoolSimulator()
                else:
                    ConfigManager.console_print(
                        "ydotool not found, falling back to pynput for input simulation."
                    )
                    return _PynputSimulator()
            else:
                return _PynputSimulator()
        elif input_method == "ydotool":
            if sys.platform == "linux":
                if cls._is_ydotool_available():
                    return _YdotoolSimulator()
                else:
                    ConfigManager.console_print(
                        "Error: 'ydotool' is not installed or not in your PATH. Falling back to 'pynput'."
                    )
                    return _PynputSimulator()
            else:
                ConfigManager.console_print(
                    "Warning: 'ydotool' is only supported on Linux. Falling back to 'pynput'."
                )
                return _PynputSimulator()
        elif input_method == "pynput":
            return _PynputSimulator()
        else:
            ConfigManager.console_print(
                f"Warning: Invalid 'input_method' value '{input_method}' in config. Using 'pynput'."
            )
            return _PynputSimulator()

    @staticmethod
    def _is_ydotool_available():
        """
        Check if ydotool is available on the system.
        
        Returns:
            bool: True if ydotool is found, False otherwise.
        """
        try:
            subprocess.run(["which", "ydotool"], check=True, capture_output=True)
            return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            return False
