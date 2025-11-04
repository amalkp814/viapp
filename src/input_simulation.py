import time
from pynput.keyboard import Controller as PynputController

from utils import ConfigManager

class InputSimulator:
    """
    A class to simulate keyboard input using pynput.
    """

    def __init__(self):
        """
        Initialize the InputSimulator.
        """
        self.keyboard = PynputController()

    def typewrite(self, text):
        """
        Simulate typing the given text with the specified interval between keystrokes.

        Args:
            text (str): The text to type.
        """
        interval = ConfigManager.get_config_value('post_processing', 'writing_key_press_delay')
        for char in text:
            self.keyboard.press(char)
            self.keyboard.release(char)
            time.sleep(interval)

    def cleanup(self):
        """
        Perform cleanup operations.
        """
        pass
