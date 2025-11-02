import sys
import time
import subprocess
import re
from pynput.keyboard import Controller as PynputController

from utils import ConfigManager

class _BaseSimulator:
    """
    A base class for input simulators that handles word replacements.
    """
    def _perform_word_replacements(self, text):
        word_replacements = ConfigManager.get_config_value('post_processing', 'word_replacements')
        if word_replacements:
            for old, new in word_replacements.items():
                # Use word boundaries to avoid replacing substrings within other words
                text = re.sub(r'\b' + re.escape(old) + r'\b', new, text, flags=re.IGNORECASE)
        return text

class _PynputSimulator(_BaseSimulator):
    """
    A class to simulate keyboard input using pynput.
    """
    def __init__(self):
        self.keyboard = PynputController()

    def typewrite(self, text):
        text = self._perform_word_replacements(text)
        interval = ConfigManager.get_config_value('post_processing', 'writing_key_press_delay')
        for char in text:
            self.keyboard.press(char)
            self.keyboard.release(char)
            time.sleep(interval)

    def cleanup(self):
        pass

class _YdotoolSimulator(_BaseSimulator):
    """
    A class to simulate keyboard input using ydotool.
    """
    def typewrite(self, text):
        text = self._perform_word_replacements(text)
        try:
            # Add a small delay to allow the user to switch windows
            time.sleep(0.1)
            subprocess.run(['ydotool', 'type', text], check=True)
        except FileNotFoundError:
            ConfigManager.console_print("Error: 'ydotool' is not installed or not in your PATH. Please install it to use this input method.")
        except Exception as e:
            ConfigManager.console_print(f"An error occurred while using ydotool: {e}")

    def cleanup(self):
        pass

class InputSimulator:
    """
    A factory class that returns the appropriate input simulator based on the configuration.
    """
    def __new__(cls):
        input_method = ConfigManager.get_config_value('post_processing', 'input_method')

        if input_method == 'auto':
            if sys.platform == 'linux':
                if cls._is_ydotool_available():
                    ConfigManager.console_print("Using ydotool for input simulation.")
                    return _YdotoolSimulator()
                else:
                    ConfigManager.console_print("ydotool not found, falling back to pynput for input simulation.")
                    return _PynputSimulator()
            else:
                return _PynputSimulator()
        elif input_method == 'ydotool':
            if sys.platform == 'linux':
                if cls._is_ydotool_available():
                    return _YdotoolSimulator()
                else:
                    ConfigManager.console_print("Error: 'ydotool' is not installed or not in your PATH. Falling back to 'pynput'.")
                    return _PynputSimulator()
            else:
                ConfigManager.console_print("Warning: 'ydotool' is only supported on Linux. Falling back to 'pynput'.")
                return _PynputSimulator()
        elif input_method == 'pynput':
            return _PynputSimulator()
        else:
            ConfigManager.console_print(f"Warning: Invalid 'input_method' value '{input_method}' in config. Using 'pynput'.")
            return _PynputSimulator()

    @staticmethod
    def _is_ydotool_available():
        try:
            subprocess.run(['which', 'ydotool'], check=True, capture_output=True)
            return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            return False
